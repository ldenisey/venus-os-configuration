#!/usr/bin/env python3

from ble-devices import BleDevices
from ble-devclass-temperature import BleDevices

class BleDevicesTeltonika(BleDevices):

    _MANUFACTURER_ID = 0x089A
    _PREFIX = "teltonika_"

    _PRODUCT_ID = 0x3042

    _classes = [BleDevClassTemperature(self._ble_dbus)]#, "Humidity", "Accelerometer", "MagnetSensor", "Battery"]
    _regs: list = [
        {
            "name": "ManufacturerID",
            "type": dbus.types.Int16
            "offset": 0,
        },
        {
            "name": "Version",
            "type": dbus.types.Byte
            "offset": 2,
        },
        {
            "name": "EyeFlags",
            "type": dbus.types.Byte
            "offset": 3,
        },
        {
            "name": "Magnet",
            "type": dbus.types.Boolean
            "offset": 3,
            "shift": 3,
            "bits": 1,
        },
        {
            "name": "LowBattery",
            "type": dbus.types.Boolean
            "offset": 3,
            "shift": 6,
            "bits": 1,
        },
        {
            "name": "Temperature",
            "type": dbus.types.Int16
            "offset": 4,
            "scale": 100
        },
        {
            "name": "Humidity",
            "type": dbus.types.Byte
            "offset": 6,
        },
        {
            "name": "MovementState",
            "type": dbus.types.Boolean
            "offset": 7,
            "bits": 1
        },
        {
            "name": "MovementCount",
            "type": dbus.types.UInt16
            "offset": 7,
            "shift": 1
        },
        {
            "name": "AnglePitch",
            "type": dbus.types.Byte
            "offset": 9,
            "xlate": byteToSignedInt
        },
        {
            "name": "AngleRoll",
            "type": dbus.types.Int16
            "offset": 10,
        },
        {
            "name": "BatteryVoltage",
            "type": dbus.types.Byte
            "offset": 12,
            "scale": 1/10,
            "bias": 2000
        },
    ]
    _settings: dict = {}

    @property
    def manufacturer_id(self) -> int:
        return _MANUFACTURER_ID

    @property
    def product_id(self) -> int:
        return _PRODUCT_ID

    @property
    def dev_prefix(self) -> str:
        return _PREFIX

    @property
    def classes(self) -> list:
        return _classes

    @property
    def regs(self) -> list:
        return _regs

    @property
    def settings(self) -> dict:
        return _settings


    def handle_mfg(self, mac: str, manufacturer_data: bytes) -> int:
        """
        Check the manufacturer data to determine if this class can manage the device, likely with a manufacturer id check.
        Returns 0 if this class can manage the device, anything else if it can't.
        """
        dev = "".join(mac.split(':')).lower()
        
        droot = self._ble_dbus.ble_dbus_create(dev, self, None)
        if droot is None:
            return 1

        self._ble_dbus.ble_dbus_set_name(droot, f"Teltonika {"".join(mac.split(':')[3:]).upper()}")

        if not self._ble_dbus.ble_dbus_is_enabled(droot):
            return 0

        # TODO parse flag to generate dynamically regs

        self._ble_dbus.ble_dbus_set_regs(droot, manufacturer_data)
        self._ble_dbus.ble_dbus_update(droot)
	
        return 0
