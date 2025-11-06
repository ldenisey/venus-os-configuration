from ble-dbus import BleDbus

class BleDevClass(object):
    
    def __init__(self, ble_dbus: BleDbus):
        self._ble_dbus = ble_dbus

    @property
    @abstractmethod
    def role(self) -> str:
        raise NotImplementedError("Subclasses must implement this variable.")

    @property
    @abstractmethod
    def settings(self) -> dict:
        """
        Optional settings that could change device behavior or data interpretation.
        """
        raise NotImplementedError("Subclasses must implement this variable, possibly with an empty dict.")

    @property
    def alarms(self) -> dict:
        """
        Configuration of the alarms that could be triggered by the device based on its data.
        """
        pass

    def init(self, droot: dict, data: dict):
        """
        Optional method executed during configuration, when the first advertising of this device has been detected.
        """
        pass

    def update(self, droot: dict, data: dict):
        """
        Optional method executed at advertising reception, after the data have been parsed to update values and settings.
        """
        pass
