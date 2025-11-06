from ble-devclass import BleDevClass
from ble-dbus import BleDbus

class BleDevClassTemperature(BleDevClass):

    _ROLE = "temperature"

    _SETTINGS = [
        {
            "name": "TemperatureType",
            "props": {
                "type": dbus.types.Int32,
                "def": 2,
                "min": 0,
                "max": 6,
            }
        }
    ]

    @property
    def role(self) -> str:
        return _ROLE

    @property
    def settings(self) -> dict:
        return _SETTINGS

    @property
    def alarms(self) -> dict:
        return None
