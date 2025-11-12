#!/usr/bin/env python3

import dbus
from ble_device import BleDevice
from dbus_settings_service import DbusSettingsService
from dbus_ble_service import DbusBleService


class BleDeviceTeltonika(BleDevice):

    MANUFACTURER_ID = 0x089A

    def __init__(self, dev_mac: str):
        super().__init__(dev_mac)

        self.info.update({
            'manufacturer_id': BleDeviceTeltonika.MANUFACTURER_ID,
            'product_id': 0x3042,
            'product_name': 'TeltonikaEyeSensor',
            # 'DeviceName': 'Teltonika EyeSensor',
            'dev_instance': 20,
            'dev_prefix': 'teltonika',
            # 'roles': ['temperature', 'digitalinput'],
            'roles': ['temperature'],
            'regs': [
                {
                    "name": "ManufacturerID",
                    "type": dbus.types.Int16,
                    "offset": 0,
                },
                {
                    "name": "Version",
                    "type": dbus.types.Byte,
                    "offset": 2,
                },
                {
                    "name": "EyeFlags",
                    "type": dbus.types.Byte,
                    "offset": 3,
                },
                {
                    "name": "Magnet",
                    "type": dbus.types.Boolean,
                    "offset": 3,
                    "shift": 3,
                    "bits": 1,
                },
                {
                    "name": "LowBattery",
                    "type": dbus.types.Boolean,
                    "offset": 3,
                    "shift": 6,
                    "bits": 1,
                },
                {
                    "name": "Temperature",
                    "type": dbus.types.Int16,
                    "offset": 4,
                    "scale": 100
                },
                {
                    "name": "Humidity",
                    "type": dbus.types.Byte,
                    "offset": 6,
                },
                {
                    "name": "MovementState",
                    "type": dbus.types.Boolean,
                    "offset": 7,
                    "bits": 1
                },
                {
                    "name": "MovementCount",
                    "type": dbus.types.UInt16,
                    "offset": 7,
                    "shift": 1
                },
                {
                    "name": "AnglePitch",
                    "type": dbus.types.Byte,
                    "offset": 9,
                    "xlate": self.byteToSignedInt
                },
                {
                    "name": "AngleRoll",
                    "type": dbus.types.Int16,
                    "offset": 10,
                },
                {
                    "name": "BatteryVoltage",
                    "type": dbus.types.Byte,
                    "offset": 12,
                    "scale": 1/10,
                    "bias": 2000
                },
            ],
        })
