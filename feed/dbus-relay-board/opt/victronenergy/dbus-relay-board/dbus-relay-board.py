#!/usr/bin/env python3

"""
Relay board dbus service.
This is a dummy service to test the dbus interface of the relay board.
"""
from gi.repository import GLib
import logging
import sys
import os
import dbus
import serial
from argparse import ArgumentParser
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.exceptions import ModbusException

# Import Victron Energy's python library.
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from logger import setup_logging
from vedbus import VeDbusService


class DbusRelayService(object):

    _CONFIG_FOLDER = '/etc/dbus-relay-board/'
    _TEMPLATE_FILE_NAME = 'template.conf'
    _VERSION = '1.0.0'

    _servicename = None
    _dbusservice: VeDbusService = None
    _protocol_handler = None

    def __init__(self, tty):

        # Find the configuration file based on this device's tty.
        config_file = self._get_conf_file(tty)
        if not config_file:
            logging.error(f"No configuration file found for tty {tty} in {self._CONFIG_FOLDER}.")
            sys.exit(1)

        ttyAlias = config_file.split('/')[-1][:-5]

        # Init dbus service
        self._servicename = f"com.victronenergy.relayboard.{ttyAlias}"
        self._dbusservice = VeDbusService(self._servicename, register=False)

        # Load configuration as a dictionary
        configuration = self._load_configuration_file(config_file)

        # Set configuration default values
        self._check_configuration(configuration)

        # Load protocol handler
        if configuration['Protocol'] == 'AT':
            logging.info("Using AT protocol handler")
            self._protocol_handler = ProtocolAT(
                tty=tty,
                baud=configuration['Baud'],
            )
        else:
            logging.info("Using RTU protocol handler")
            self._protocol_handler = ProtocolRTU(
                tty=tty,
                baud=configuration['Baud'],
                parity=configuration.get('Parity', 0),
                stopBits=configuration.get('StopBits', 1)
            )

        # Create the management objects, cf https://github.com/victronenergy/venus/wiki/dbus-api
        self._dbusservice.add_mandatory_paths(
            processname=__file__,
            processversion=self._VERSION,
            connection='Relay board ' + ttyAlias,
            deviceinstance=256,  # cf https://github.com/victronenergy/venus/wiki/dbus-api#vrm-device-instances
            productid=0x2042,  # Available based on https://www.victronenergy.com/api/v1/products/?format=json
            productname='Relay board ' + ttyAlias,
            firmwareversion=1,
            hardwareversion=1,
            connected=1
        )

        # Set configuration
        self._dbusservice.add_path('/CustomName', configuration['CustomName'], writeable=True, valuetype=dbus.String)
        self._dbusservice.add_path('/Baud', configuration['Baud'], writeable=False, valuetype=dbus.UInt32)
        self._dbusservice.add_path('/Protocol', configuration['Protocol'], writeable=False, valuetype=dbus.String)
        self._dbusservice.add_path(
            '/RelayNumber', configuration['RelayNumber'], writeable=False, valuetype=dbus.UInt16)
        for i in range(0, configuration['RelayNumber']):
            self._dbusservice.add_path(
                f"/Relay/{i}/ProductName", f"Relay {i+1}", writeable=False, valuetype=dbus.String)
            self._dbusservice.add_path(
                f"/Relay/{i}/CustomName", configuration.get(f"Relay_{i}_CustomName", ''), writeable=True, valuetype=dbus.String)
            self._dbusservice.add_path(
                f"/Relay/{i}/State", self._protocol_handler.get_relay_state(i), writeable=True, valuetype=dbus.UInt16, onchangecallback=self._on_relay_state_change)

        self._dbusservice.register()

    def _get_conf_file(self, tty: str) -> str:
        for file in os.listdir(self._CONFIG_FOLDER):
            if file == self._TEMPLATE_FILE_NAME:
                continue  # Skip the template file
            if file.endswith('.conf'):
                logging.debug(f"Found configuration file: {file}")
                dev_file = os.path.join('/dev', file[:-5])
                if not os.path.exists(dev_file):
                    logging.warning(f"Found a misnamed configuration file: {file}")
                    continue
                dev_file_real_path = os.path.realpath(dev_file)
                if dev_file_real_path.endswith(tty):
                    logging.info(f"Using configuration file: {file} for tty {tty}")
                    return os.path.join(self._CONFIG_FOLDER, file)
        return None

    def _load_configuration_file(self, config_file_path: str) -> dict:
        try:
            with open(config_file_path, 'r') as f:
                configuration = {}
                for line in f:
                    if line.startswith('#') or not line.strip() or '=' not in line:
                        continue  # Skip comments, empty or malformed lines
                    key, value = line.split('=', 1)
                    value = value.split('#', 1)[0].strip()  # Remove comments
                    configuration[key.strip()] = value.strip()
                return configuration
        except (IOError, OSError) as e:
            logging.error(f"Error reading configuration file {config_file_path}: {e}")
            sys.exit(1)

    def _check_configuration(self, configuration: dict):
        configuration['CustomName'] = configuration.get('CustomName', '')
        configuration['Protocol'] = configuration.get('Protocol', 'RTU')

        for key, value in {'Baud': 9600, 'Parity': 0, 'StopBits': 1, 'RelayNumber': 1}.items():
            if configuration.get(key) is None:
                configuration[key] = value
            else:
                try:
                    configuration[key] = int(configuration[key])
                except ValueError:
                    logging.error(f"Invalid {key} in configuration file. Must be an integer.")
                    sys.exit(1)

    def _on_relay_state_change(self, path, value):
        _path_split = path.split('/')
        if _path_split[1] == 'Relay':
            index = int(_path_split[2])
            if value not in (0, 1):
                logging.error(f"Invalid value for relay {index}: {value}. Must be 0 or 1.")
                return False
            self._protocol_handler.set_relay_state(index, value)
        return True


class ProtocolAT:

    _tty: str = None
    _baud: int = None

    def __init__(self, tty: str, baud: int):
        self._tty = '/dev/' + tty
        self._baud = baud
        _serial: serial.Serial = None
        try:
            _serial = serial.Serial(self._tty, self._baud, timeout=1)
        except serial.SerialException as e:
            logging.error(f"Failed to open serial port {tty}: {e}")
            sys.exit(1)
        finally:
            if not _serial is None:
                _serial.close()

    def get_relay_state(self, index: int) -> int:
        logging.info(f"Getting state for relay {index}")
        board_index = index + 1
        response = self._send_command(f"AT+R{board_index}")
        if f"Close{board_index}" in response:
            logging.info(f"Relay {index} has state: 0")
            return 0
        elif f"Open{board_index}" in response:
            logging.info(f"Relay {index} has state: 1")
            return 1
        else:
            logging.error(f"Unexpected response from relay board: {response}")
            return None

    def set_relay_state(self, index: int, state: int) -> bool:
        logging.info(f"Setting relay {index} to state {state}")
        board_index = index + 1
        response = self._send_command(f"AT+{'O' if state else 'C'}{board_index}")
        if f"Open{board_index}" in response and state:
            logging.info(f"Relay {index} successfully set to state {state}")
            return True
        elif f"Close{board_index}" in response and not state:
            logging.info(f"Relay {index} successfully set to state {state}")
            return True
        else:
            logging.error(f"Failed to set relay {index} to state {state}")
            return False

    def _send_command(self, command: str) -> str:
        _serial: serial.Serial = None
        try:
            _serial = serial.Serial(self._tty, self._baud, timeout=1)

            logging.debug(f"Sending command: {command}")
            _serial.write(command.encode('utf-8'))

            while True:  # Read lines until a non-blank line is found
                response = _serial.readline().decode('utf-8').strip()
                if response:
                    break
            logging.debug(f"Command response: {response}")
            return response
        finally:
            if not _serial is None:
                _serial.close()


class ProtocolRTU:

    _client: ModbusSerialClient = None

    def __init__(self, tty: str, baud: int, parity: int, stopBits: int):
        self._client = ModbusSerialClient(
            name=os.path.basename(__file__),
            port='/dev/' + tty,
            timeout=1,
            retries=3,
            method='rtu',
            baudrate=baud,
            bytesize=8,
            parity={0: 'N', 1: 'O', 2: 'E'}.get(parity, 'N'),
            stopbits=stopBits,
        )

        # Testing connection
        try:
            if not self._client.connect():
                logging.error(f"Failed to connect to Modbus RTU device on {tty} at {baud} baud.")
                sys.exit(1)
        finally:
            self._client.close()

    def get_relay_state(self, index: int) -> int:
        logging.info(f"Getting state for relay {index}")
        try:
            self._client.connect()
            result = self._client.read_coils(index, 1, unit=1)
            state = 1 if result.bits[0] else 0
            logging.info(f"Relay {index} has state: {state}")
            return state
        finally:
            self._client.close()

    def set_relay_state(self, index: int, state: int) -> bool:
        logging.info(f"Setting relay {index} to state {state}")
        try:
            self._client.connect()
            result = self._client.write_coil(index, (state == 1), unit=1)
            if result.isError():
                logging.error(f"Failed to set relay {index} to state {state}")
                return False
            else:
                logging.info(f"Relay {index} successfully set to state {state}")
                return True
        except ModbusException as e:
            logging.error(f"Failed to set relay {index} to state {state}: {e}")
            return False
        finally:
            self._client.close()


def main():
    parser = ArgumentParser(description=sys.argv[0])
    parser.add_argument('--tty', help='Relay board tty name', type=str, required=True, action='store')
    parser.add_argument('--debug', help='Turn on debug logging', default=False, action='store_true')
    args = parser.parse_args()
    logger = setup_logging(args.debug)

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

    pvac_output = DbusRelayService(tty=args.tty)

    logging.info('Connected to dbus, and switching over to GLib.MainLoop() (= event based)')
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
