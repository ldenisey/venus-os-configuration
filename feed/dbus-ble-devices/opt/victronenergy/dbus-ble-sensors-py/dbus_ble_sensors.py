#!/usr/bin/env python3

"""
Teltonika eye sensor dbus service.
"""
import asyncio
from gi.repository import GLib
import logging
import sys
import os
import importlib.util
import inspect
from dbus.mainloop.glib import DBusGMainLoop
from argparse import ArgumentParser
from ble_dbus import BleDbus
from ble_devices import BleDevices

# Import Victron Energy's python library.
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from logger import setup_logging

# Import ble library
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext'))
import gbulb
import bleak


class DbusBleSensorsService(object):

    _SCAN_TIMEOUT = 5 #15
    _SCAN_INTERVAL_STANDARD = 10 #90

    ble_dbus: BleDbus = None
    

    def __init__(self):
        self._device_classes = {}

        # Init dbus
        ble_dbus = BleDbus()

        # Load configurations
        self._load_configs()


    def load_device_classes(self):
        # Loading manufacturer specific classes
        for filepath in os.path.dirname(os.path.abspath(__file__)):
            filename = os.path.basename(file_path)
            if filename.startswith('ble-devices-') and filename.endswith('.py'):
                module_name = os.path.splitext(os.path.basename(filepath))[0]

                # Import the module from file
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                except Exception:
                    logging.warning(f"Can not import file {filepath}.")
                    continue

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__ == module.__name__ and issubclass(obj, BleDevices) and obj is not BleDevices:
                        instance = obj(self.ble_dbus)
                        self._device_classes[instance.manufacturer_id] = instance
                        break


    def ble_handle_mfg(self, mac: str, manufacturer_data: bytes) -> int:
        for man_id, man_data in manufacturer_data.items():
            handler = self._devices_classes.get(man_id, None)
            if handler is not None:
                return handler.handle_mfg(mac, manufacturer_data)
        return 1


    async def _scan(self, adapter: str):
        def _scan_callback(device, advertisement_data) -> int:
            mac = device.address
            logging.debug(f"Found device: {mac} {device.name} {advertisement_data}")
            if advertisement_data.manufacturer_data is None or len(advertisement_data.manufacturer_data) < 1:
                return 1
            for man_id, man_data in advertisement_data.manufacturer_data.items():
                ret = self.ble_handle_mfg(mac, man_data)
                if ret == 0:
                    return 0
            return 2

        logging.info(f"{adapter} - Scanning ...")
        try:
            await bleak.BleakScanner.discover(
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
            scan_tasks = [ asyncio.create_task(self._scan(adapter)) for adapter in ble_dbus._adapters ]
            await asyncio.gather(*scan_tasks)

            if ble_dbus.get_cont_scan():
                logging.info(f"Continuous scan: restarting scan")
            else:
                delay = _SCAN_INTERVAL_STANDARD - _SCAN_TIMEOUT
                logging.info(f"Standard scan: pausing scan for {delay} seconds")
                await asyncio.sleep(delay)


def main():
    parser = ArgumentParser(description=sys.argv[0])
    parser.add_argument('--debug', '-d', help='Turn on debug logging', default=False, action='store_true')
    parser.add_argument('--noscan', '-n', help='Turn off scanning', default=False, action='store_true')
    args = parser.parse_args()
    logger = setup_logging(args.debug)

    # Init gbulb, configure GLib and integrate asyncio in it
    gbulb.install()
    DBusGMainLoop(set_as_default=True)
    asyncio.set_event_loop_policy(gbulb.GLibEventLoopPolicy())

    pvac_output = DbusBleDevicesService()

    logging.info('Connected to dbus, starting main loop')
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
