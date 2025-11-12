#!/usr/bin/env python3

import asyncio
from gi.repository import GLib
import logging
import sys
import os
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from argparse import ArgumentParser
from ble_device import BleDevice
from ble_role import BleRole
from dbus_ble_service import DbusBleService
from dbus_settings_service import DbusSettingsService

# Import ble library
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext'))
import bleak
import gbulb

# Import Victron Energy's python library.
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from logger import setup_logging


class DbusBleSensors(object):
    # Main class for the D-bus BLE Sensors python service. Extend base C service 'dbus-ble-sensors'
    # to allow community integration of unsupported (by Victron Energy team) BLE sensors.
    # TODO: Handle timeout
    # TODO: Handle scanning conflicts with VE dbus-ble-sensors
    # Cf.
    # - https://github.com/victronenergy/dbus-ble-sensors/
    # - https://github.com/victronenergy/node-red-contrib-victron/blob/master/src/nodes/victron-virtual.js
    # - https://github.com/victronenergy/gui-v2/blob/main/data/mock/conf/services/tank-lpg.json
    # - https://github.com/victronenergy/dbus-recorder/blob/master/demo2_water.csv
    # - https://github.com/victronenergy/gui-v2/blob/main/data/mock/conf/services/ruuvi-salon.json

    os.environ["PROCESS_NAME"] = os.path.basename(os.path.dirname(__file__))
    os.environ["PROCESS_VERSION"] = '1.0.0'

    _SCAN_TIMEOUT = 5  # 15
    _SCAN_INTERVAL_STANDARD = 10  # 90

    def __init__(self):
        # Get dbus, default is system
        self._dbus: dbus.Bus = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()
        # Accessor to dbus settings service (default : com.victronenergy.settings)
        self._dbus_settings_service = DbusSettingsService()
        # Accessor to dbus ble dedicated service (default : com.victronenergy.ble)
        self._dbus_ble_service = DbusBleService(True)

        # Initialze BT adapters search
        self._adapters = []
        self._list_adapters()

        # Load definition classes
        BleRole.load_role_classes(os.path.abspath(__file__))
        BleDevice.load_device_classes(os.path.abspath(__file__))

    def _list_adapters(self):
        # Adding callback for futur connections/disconnections
        self._dbus.add_signal_receiver(
            self._on_interfaces_added,
            dbus_interface='org.freedesktop.DBus.ObjectManager',
            signal_name='InterfacesAdded'
        )
        self._dbus.add_signal_receiver(
            self._on_interfaces_removed,
            dbus_interface='org.freedesktop.DBus.ObjectManager',
            signal_name='InterfacesRemoved'
        )

        # Initial search for adapters
        object_manager = dbus.Interface(
            self._dbus.get_object('org.bluez', '/'),
            'org.freedesktop.DBus.ObjectManager'
        )
        objects = object_manager.GetManagedObjects()
        for path, ifaces in objects.items():
            self._on_interfaces_added(path, ifaces)

    def _on_interfaces_added(self, path, interfaces):
        if not str(path).startswith('/org/bluez'):
            return
        logging.debug(f"Interfaces added callback: {path}, {interfaces}")
        if 'org.bluez.Adapter1' in interfaces:
            adapter = self._dbus.get_object('org.bluez', path)
            props = dbus.Interface(adapter, 'org.freedesktop.DBus.Properties')
            mac = props.Get('org.bluez.Adapter1', 'Address')
            name = path.split('/')[-1]
            # Saving adapter
            if name == 'hci1':  # TODO debug and remove
                logging.info(f"Skipping adapter {name}")
                return
            logging.info(f"Adding adapter {name} found at {path} with address: {mac}")
            self._adapters.append(name)
            self._dbus_ble_service.add_ble_adapter(name, mac)

    def _on_interfaces_removed(self, path, interfaces):
        if not str(path).startswith('/org/bluez'):
            return
        logging.debug(f"Interfaces removed callback: {path}, {interfaces}")
        if 'org.bluez.Adapter1' in interfaces:
            # Remove adapter
            name = path.split('/')[-1]
            self._dbus_ble_service.remove_ble_adapter(name)
            self._adapters.remove(name)
            logging.info(f"Adapter removed at {path}")

    async def _scan(self, adapter: str):
        def _scan_callback(device, advertisement_data):
            logging.debug(f"Scanned device: {device.name} {device.address} {advertisement_data}")
            if advertisement_data.manufacturer_data is None or len(advertisement_data.manufacturer_data) < 1:
                logging.debug(f"Ignoring device {device.name} {device.address}: no manufacturer data")
                return

            dev_mac = "".join(device.address.split(':')).lower()

            # First time device initialization
            # Loop through manufacturer data fields, even though most devices only use one
            for man_id, man_data in advertisement_data.manufacturer_data.items():
                if (dev_instance := BleDevice.get(dev_mac)) is None:
                    device_class = BleDevice.DEVICE_CLASSES.get(man_id, None)
                    if device_class is None:
                        logging.debug(
                            f"Ignoring device {device.name} {device.address}: no device class for manufacturer id {man_id}")
                        return

                    # Run device specific parsing
                    logging.debug(f"Initializing device class {device_class} for: {device.name} {device.address}")
                    dev_instance = device_class(dev_mac)
                    dev_instance.init()

                # Parsing data
                logging.debug(f"Parsing data for device: {device.name} {device.address}")
                dev_instance.handle_mfg(man_data)

        logging.info(f"{adapter} - Scanning ...")
        try:
            await bleak.BleakScanner.discover(  # TODO force timeout
                timeout=self._SCAN_TIMEOUT,
                adapter=adapter,
                return_adv=True,
                detection_callback=_scan_callback
            )
            logging.info(f"{adapter} - Scan finished")
        except Exception as e:
            logging.error(f"{adapter} - Scan error: {e}")

    async def scan_loop(self):
        while True:
            logging.info(f"Adapters: {self._adapters}")
            scan_tasks = [asyncio.create_task(self._scan(adapter)) for adapter in self._adapters]
            await asyncio.gather(*scan_tasks)

            if self._dbus_ble_service.get_continuous_scanning():
                logging.info(f"Continuous scan: restarting scan")
            else:
                delay = self._SCAN_INTERVAL_STANDARD - self._SCAN_TIMEOUT
                logging.info(f"Standard scan: pausing scan for {delay} seconds")
                await asyncio.sleep(delay)


def main():
    parser = ArgumentParser(description=sys.argv[0])
    parser.add_argument('--debug', '-d', help='Turn on debug logging', default=False, action='store_true')
    parser.add_argument('--noscan', '-n', help='Turn off scanning', default=False, action='store_true')
    args = parser.parse_args()
    logger = setup_logging(args.debug)
    logging.info(f"Starting with arguments: --debug={args.debug} --noscan={args.noscan}")

    # Init gbulb, configure GLib and integrate asyncio in it
    gbulb.install()
    DBusGMainLoop(set_as_default=True)
    asyncio.set_event_loop_policy(gbulb.GLibEventLoopPolicy())

    pvac_output = DbusBleSensors()

    mainloop = asyncio.new_event_loop()
    asyncio.set_event_loop(mainloop)
    if not args.noscan:
        logging.info('Starting scan loop')
        asyncio.get_event_loop().create_task(pvac_output.scan_loop())
    else:
        logging.info('Skipping scan loop')
    mainloop.run_forever()


if __name__ == "__main__":
    main()
