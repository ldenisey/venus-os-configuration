from __future__ import annotations
import os
import sys
import inspect
import logging
import importlib.util
import dbus
from dbus_ble_service import DbusBleService
from dbus_device_service import DbusDeviceService
from ble_role import BleRole


class BleDevice(object):

    _SIGNED_TYPES = [dbus.types.Int16, dbus.types.Int32, dbus.types.Int64]

    MANUFACTURER_ID = 0  # To be overloaded in children classes: int, ble manufacturer id

    # Dict of devices classes, key is manufacturer id
    DEVICE_CLASSES = {}

    # Dict of already initialized instances, key is mac address
    DEVICE_INSTANCES = {}

    def __init__(self, dev_mac: str):
        self._dbus_services: dict = {}

        # Mandatory fields must be overloaded by subclasses, optional ones can be left as is.
        self.info = {
            'dev_mac': dev_mac,         # Internal
            'product_id': 0x0000,       # Mandatory, int, ble product id
            'product_name': None,       # Mandatory, str, product name without spaces or special chars
            'hardware_version': "1.0.0",  # Optional,  str, Device harware version
            'firmware_version': "1.0.0",  # Optional,  str, Device firmware version
            'DeviceName': None,         # Mandatory, str, human friendly device name, i.e. Ruuvi AABB
            'dev_prefix': None,         # Mandatory, str, device prefix, used in dbus path, must be short, without spaces
            'roles': [],                # Mandatory, list of str, roles that this device can have: temperature, tank, battery, digitalinput, humidity
            # Mandatory, list of dict representing the device advertising data with the following keys :
            'regs': [],
            'dev_instance': 20,         # Optional,  int, base internal id that will be incremented to be unique
            # - offset : byte offset, i.e. data start position
            # - shift	 : bit offset, in case the data is not "byte aligned"
            # - type   : type of the data
            # - bits   : length of the data in bits, mandatory if type is not set
            # - scale  : scale of the data, used with bias to compute the data with : data / scale + bias
            # - bias   : bias to be applied with the scale
            # - flags  : Can be : REG_FLAG_BIG_ENDIAN, REG_FLAG_INVALID
            # - inval  : If flag REG_FLAG_INVALID is set, value that will invalidate the data and have it ignored
            # - xlate  : Name of a method to be executed after data parsing
            # - format : Format of the data
            # Optional,  list of dict, settings that could change device behavior or data interpretation.
            'settings': [],
            'alarms': [],               # Optional,  list of dict, possible alarms raised by the device, defined with :
            # - name      : Name of the alarm
            # - item      : Type of alarm to raise
            # - flags     : list of :
            #    - "ALARM_FLAG_CONFIG" if the alarm targets a config
            #    - "ALARM_FLAG_HIGH" if the alarm should be triggered when data is higher than level
            # - level     : Float value defining the alarm level
            # - get_level : Name of a method to compute level if needed
            # - hyst      : Hysterisis value to add to level when the alarm is active
            # - active    : &high_active_props
            # - restore   : &high_restore_props
            #
            # - name	  : "High",
            # - item	  : "Level",
            # - flags	  : ALARM_FLAG_HIGH | ALARM_FLAG_CONFIG,
            # - active  : &high_active_props,
            # - restore : &high_restore_props,
            #
            # .name	= "LowBattery",
            # .item	= "BatteryVoltage",
            # .hyst	= 0.4,
            # .get_level = ruuvi_lowbat,
            #
            # .name	= "LowBattery",
            # .item	= "BatteryVoltage",
            # .level	= 3.2,
            # .hyst	= 0.4,
            'data': {},                 # Optional,  dict, custom dict for storing specific data to be passed to custom role and device methods
        }

    def init(self):
        """
        Optional overload, executed during configuration when the first advertising of this device has been detected.
        """
        # Setting configuration
        BleDevice.DEVICE_INSTANCES['dev_mac'] = self
        self.check_configuration()
        self.load_configuration()

        logging.info(f"Initializing device {self.info['DeviceName']} {self.info['dev_mac']} ...")

        # Setting ble service
        self.configure_dbus_ble_service()

        # Settings device services (one service per role)
        self.load_dbus_services()
        for dbus_service in self._dbus_services.values():
            self.init_device_dbus_service(dbus_service)
        logging.info(f"Device {self.info['DeviceName']} {self.info['dev_mac']} initialized")

    def handle_mfg(self, manufacturer_data: bytes):
        """
        Optional overload, check product id to adapt to various harware if any and/or implement specific parsing logic.
        Returns 0 if this class can manage the device, anything else if it can't.
        """
        logging.info(f"Parsing advertising from device {self.info['DeviceName']} {self.info['dev_mac']}")

        if not self.is_enabled():
            return

        # Parse data
        sensor_data: dict = self.parse_manufacturer_data(manufacturer_data)
        for dbus_service in self._dbus_services:
            # Update sensors data
            self.update_values(dbus_service, sensor_data)

            # Update alarm states
            dbus_service.ble_role.update(self, sensor_data)
            for alarm in dbus_service.ble_role.info['alarms']:
                self.update_alarm(dbus_service, alarm)
            for alarm in self.info['alarms']:
                self.update_alarm(dbus_service, alarm)

            # Start service if needed
            dbus_service.connect()

        # Reset timeout
        self.info['tick'] = 0


# /!\/!\/!\/!\/!\/!\  Methods below should not been overrided  /!\/!\/!\/!\/!\/!\

    @staticmethod
    def get(mac: str) -> BleDevice:
        return BleDevice.DEVICE_INSTANCES.get('dev_mac', None)

    @staticmethod
    def load_device_classes(execution_path: str):
        logging.info("Loading device classes ...")
        device_classes_prefix = f"{os.path.splitext(os.path.basename(__file__))[0]}_"

        # Loading manufacturer specific classes
        for filename in os.listdir(os.path.dirname(execution_path)):
            if filename.startswith(device_classes_prefix) and filename.endswith('.py'):
                module_name = os.path.splitext(filename)[0]

                # Import the module from file
                logging.debug(f"Loading device class {filename} ...")
                spec = importlib.util.spec_from_file_location(module_name, filename)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Check and import
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__ == module.__name__ and issubclass(obj, BleDevice) and obj is not BleDevice:
                        # instance = obj(dbus_ble_service, dbus_settings_service)
                        # instance.check_configuration()
                        BleDevice.DEVICE_CLASSES[obj.MANUFACTURER_ID] = obj
                        break
                logging.debug(f"Device class {filename} loaded")
        logging.info(f"Device classes loaded: {BleDevice.DEVICE_CLASSES}")

    @staticmethod
    def byteToSignedInt(byte: bytes) -> int:
        return byte if byte < 128 else byte - 256

    def check_configuration(self):
        for key in ['manufacturer_id', 'product_id', 'product_name', 'dev_instance', 'dev_prefix', 'roles', 'regs', 'settings', 'alarms']:
            if key not in self.info:
                raise ValueError(f"Configuration '{key}' is missing")
            if self.info[key] is None:
                raise ValueError(f"Configuration '{key}' can not be None")

        for number in ['manufacturer_id', 'product_id', 'dev_instance']:
            if not isinstance(self.info[number], int):
                raise ValueError(f"Configuration '{number}' must be an integer")

        for list_key in ['roles', 'regs', 'settings', 'alarms']:
            if not isinstance(self.info[list_key], list):
                raise ValueError(f"Configuration '{list_key}' must be a list")

        for list_mandatory in ['roles', 'regs']:
            if self.info[list_mandatory].__len__() < 1:
                raise ValueError(f"Configuration '{list_mandatory}' must be contains at least one element")

        for index, setting in enumerate(self.info['settings']):
            if 'name' not in setting:
                raise ValueError(
                    f"Missing 'name' in setting at index {index} of {self.info['DeviceName']} device class")
            if 'props' not in setting:
                raise ValueError(
                    f"Missing 'props' definition in setting {setting['name']} of {self.info['DeviceName']} device class")
            for key in ['def', 'min', 'max']:
                if key not in setting['props']:
                    raise ValueError(
                        f"Missing key '{key}' in setting {setting['name']} of {self.info['DeviceName']} device class")

        for index, alarm in enumerate(self.info['alarms']):
            if 'name' not in alarm:
                raise ValueError(f"Missing 'name' in alarm at index {index} of {self.info['DeviceName']} device class")
            for key in ['item', 'active', 'restore']:
                if key not in alarm:
                    raise ValueError(
                        f"Missing key '{key}' in alarm {alarm['name']} of {self.info['DeviceName']} device class")
            for sig in ['active', 'restore']:
                for key in ['def', 'min', 'max']:
                    if key not in alarm[sig]:
                        raise ValueError(
                            f"Missing key '{key}' in field {sig} of alarm {alarm['name']} of {self.info['DeviceName']} device class")
            if (alarm.get('flags', None) and 'ALARM_FLAG_CONFIG' not in alarm['flags']) and alarm.get('level', None) is None and alarm.get('getlevel', None) is None:
                raise ValueError(
                    f"Alarm {alarm['name']} of {self.info['DeviceName']} device class must define a level. Set 'level' or 'getlevel' fields or use dbus configuration with 'ALARM_FLAG_CONFIG' flag.")

    def load_configuration(self):
        self.info['manufacturer_id'] = self.MANUFACTURER_ID
        self.info['dev_id'] = self.info['dev_prefix'] + '_' + self.info['dev_mac']
        self.info['DeviceName'] = self.info['DeviceName'] + ' ' + self.info['dev_mac'][0:4].upper()
        self.info['dbus_settings_root'] = f"/Settings/Devices/{self.info['dev_id']}"
        self.info['dbus_ble_root'] = f"/Devices/{self.info['dev_id']}"
        self.info['services'] = {}  # Dict role/dbus service
        self.info['tick'] = 0

    def on_enabled_changed(self, new_enabled_value: int):
        for dbus_service in self._dbus_services.value():
            if new_enabled_value:
                dbus_service.connect()
            else:
                dbus_service.disconnect()

    def configure_dbus_ble_service(self):
        # Set name
        DbusBleService.get().set_device_name(self.info)

        # Init Enabled setting
        DbusBleService.get().init_enabled_status(self.info, self.on_enabled_changed)

    def load_dbus_services(self):
        for role_name in self.info['roles']:
            if (role_instance := BleRole.get_role_instance(role_name)) is None:
                raise ValueError(f"Can not find role '{role_name}' declared in device class {self.info['DeviceName']}")

            logging.debug(f"Adding role '{role_name}' instance to device '{self.info['DeviceName']}'")
            self._dbus_services[role_name] = DbusDeviceService(self, role_instance)

    def init_settings(self, dbus_service: DbusDeviceService, settings: list):
        for setting in settings:
            dbus_service.add_setting(setting)
            if setting.get('onchange', None) is not None:
                getattr(self, setting['onchange'])(self, setting)

    def init_alarms(self, dbus_service: DbusDeviceService, alarms: list):
        for alarm in alarms:
            if 'ALARM_FLAG_CONFIG' in alarm.get('flags'):
                dbus_service.add_alarm(alarm)

    def init_device_dbus_service(self, dbus_service: DbusDeviceService):
        dbus_service.init_custom_name()

        self.init_settings(dbus_service, dbus_service.ble_role.info['settings'])
        self.init_alarms(dbus_service, dbus_service.ble_role.info['alarms'])

        dbus_service.ble_role.init(self)

        self.init_settings(dbus_service, self.info['settings'])
        self.init_alarms(dbus_service, self.info['alarms'])

    def is_enabled(self) -> bool:
        return DbusBleService.get().is_device_enabled(self.info)

    def load_int(self, reg: dict, manufacturer_data: bytes) -> any:
        offset: int = reg['offset']  # TODO check if it is mandatory, else set default value
        flags: list = reg.get('flags', [])
        shift: int = reg.get('shift', 0)
        _type = reg['type']

        # Get data length
        if (bits := reg.get('bits', None)) is None:
            return None
        else:
            match _type:
                case dbus.types.Boolean | dbus.types.Byte:
                    bits = 8
                case dbus.types.Int16 | dbus.types.UInt16:
                    bits = 16
                case dbus.types.Int32 | dbus.types.UInt32:
                    bits = 32
                case dbus.types.Int64 | dbus.types.UInt64:
                    bits = 64
                case _:
                    return None

        # Check there is enough data for the expected value
        size = (bits + shift + 7) >> 3
        if size > len(manufacturer_data) - offset:
            return None

        # Read data
        value = int.from_bytes(
            manufacturer_data[offset:offset + size],
            'big' if flags.contains("REG_FLAG_BIG_ENDIAN") else 'little',
            _type in BleDevice._SIGNED_TYPES
        )

        # Applying shift and triming on bits size
        value = (value >> shift) << 64 - bits >> 64 - bits

        # Post actions
        if flags.contains("REG_FLAG_INVALID") and value == reg.get('inval', None):
            return None
        elif xlate := reg.get('xlate', None):
            return getattr(self, xlate)(self.droot, value)  # TODO rethink
        elif scale := reg.get('scale', None):
            return value / scale + reg.get('bias', 0)
        else:
            return value

    def parse_manufacturer_data(self, manufacturer_data: bytes) -> dict:
        # TODO parse flag to generate dynamically regs
        values = {}
        for reg in self.info['regs']:
            value = None
            match reg['type']:
                case dbus.types.Boolean:
                    value = bool(self.load_int(reg, manufacturer_data))
                case dbus.types.Byte | dbus.types.Int16 | dbus.types.UInt16 | dbus.types.Int32 | dbus.types.UInt32 | dbus.types.Int64 | dbus.types.UInt64:
                    value = self.load_int(reg, manufacturer_data)
                case dbus.types.Double:
                    pass
                case dbus.types.String:
                    pass
                case dbus.types.ObjectPath | dbus.types.Signature | dbus.types.Array | dbus.types.Dictionary | dbus.types.ByteArray | dbus.types.Variant:
                    pass
                case _:
                    pass

            if value is None:
                continue

            values[reg['name']] = value
        return values

    def update_data(self, dbus_service: DbusDeviceService, sensor_data: dict):
        for name, value in sensor_data.items():
            dbus_service.set_value(name, value)

    def update_alarm(self, dbus_service: DbusDeviceService, alarm: dict):
        # Is alarm enabled ?
        if not dbus_service.is_alarm_enabled(alarm):
            return

        # Is alarm active ?
        active = dbus_service.get_alarm_active_status(alarm)

        # Get alarm level (i.e. threshold)
        if 'ALARM_FLAG_CONFIG' in alarm['flags']:
            level = dbus_service.get_alarm_level(alarm, active)
        else:
            if alarm.get('get_level', None):
                # TODO Make it work for role classes
                level = getattr(self, alarm['get_level'])(self.droot, alarm)
            else:
                level = alarm['level']
            if active:
                level += alarm.get('hyst', 0)

        # Compare level to latest sensor value
        sensor_value = float(dbus_service.get_value(alarm['item']))
        active = sensor_value > level if "ALARM_FLAG_HIGH" in alarm['flags'] else sensor_value < level
        dbus_service.set_alarm_active_status(alarm, active)
