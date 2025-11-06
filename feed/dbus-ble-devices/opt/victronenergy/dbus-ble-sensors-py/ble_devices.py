from ble-dbus import BleDbus

class BleDevices(object):
    
    def __init__(self, ble_dbus: BleDbus):
        self._ble_dbus = ble_dbus

    @property
    @abstractmethod
    def manufacturer_id(self) -> int:
        raise NotImplementedError("Subclasses must implement this variable.")

    @property
    @abstractmethod
    def product_id(self) -> int:
        raise NotImplementedError("Subclasses must implement this variable.")

    @property
    @abstractmethod
    def dev_prefix(self) -> str:
        raise NotImplementedError("Subclasses must implement this variable.")

    @property
    def role(self) -> str:
        raise NotImplementedError("Subclasses must implement this variable, possibly with None.")

    @property
    @abstractmethod
    def classes(self) -> list:
        """
        List of classes of the device : Temperature, Humidity, ...
        """
        raise NotImplementedError("Subclasses must implement this variable.")

    @property
    @abstractmethod
    def regs(self) -> list:
        """
        Structure of the device advertising data. List of dict with the following keys :
        - offset : byte offset, i.e. data start position
        - shift	 : bit offset, in case the data is not "byte aligned" 
        - type   : type of the data
        - bits   : length of the data in bits, mandatory if type is not set
        - scale  : scale of the data, used with bias to compute the data with : data / scale + bias
        - bias   : bias to be applied with the scale
        - flags  : Can be : REG_FLAG_BIG_ENDIAN, REG_FLAG_INVALID
        - inval  : If flag REG_FLAG_INVALID is set, value that will invalidate the data and have it ignored
        - xlate  : Name of a method to be executed after data parsing
        - format : Format of the data
        """
        raise NotImplementedError("Subclasses must implement this variable.")

    @property
    @abstractmethod
    def settings(self) -> list:
        """
        Optional settings that could change device behavior or data interpretation.
        """
        raise NotImplementedError("Subclasses must implement this variable, possibly with an empty dict.")

    @property
    @abstractmethod
    def alarms(self) -> list:
        """
        Configuration of the alarms that could be triggered by the device based on its data.
        List of dict containing the following :
        - name      : Name of the alarm
        - item      : Type of alarm to raise
        - flags     : list of :
            - "ALARM_FLAG_CONFIG" if the alarm targets a config
            - "ALARM_FLAG_HIGH" if the alarm should be triggered when data is higher than level
        - level     : Float value defining the alarm level
        - get_level : Name of a method to compute level if needed
        - hyst      : Hysterisis value to add to level when the alarm is active
		- active    : &high_active_props
		- restore   : &high_restore_props

        - name	  : "High",
		- item	  : "Level",
		- flags	  : ALARM_FLAG_HIGH | ALARM_FLAG_CONFIG,
		- active  : &high_active_props,
		- restore : &high_restore_props,

        .name	= "LowBattery",
		.item	= "BatteryVoltage",
		.hyst	= 0.4,
		.get_level = ruuvi_lowbat,

		.name	= "LowBattery",
		.item	= "BatteryVoltage",
		.level	= 3.2,
		.hyst	= 0.4,
        """
        raise NotImplementedError("Subclasses must implement this variable, possibly with an empty dict.")


    def init(self, droot: dict, data: dict):
        """
        Optional method executed during configuration, when the first advertising of this device has been detected.
        """
        pass


    @abstractmethod
    def handle_mfg(self, mac: str, manufacturer_data: bytes) -> int:
        """
        Handle manufacturing data.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def byteToSignedInt(self, byte: bytes) -> int:
        return byte if byte< 128 else byte- 256
