-#!/usr/bin/env python3

import logging
import sys
import os
import json
import dbus

# Import Victron Energy's python library.
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from vedbus import VeDbusService, VeDbusItemImport, VeDbusItemExport, VeDbusTreeExport
from vedbus_utils import *
from settingsdevice import SettingsDevice


class BleDbus(object):

    _VERSION = '1.0.0'
    _BLE_SERVICENAME = 'com.victronenergy.ble'
    _BLE_CONTSCAN_PATH = '/ContinuousScan'
    _SETTINGS_SERVICENAME = 'com.victronenergy.settings'
    _SETTINGS_CONTSCAN_PATH = '/Settings/BleSensors/ContinuousScan'

    _SIGNED_TYPES = [dbus.types.Int16, dbus.types.Int32, dbus.types.Int64]

    def __init__(self):
        self._bus: dbus.Bus = None
        self._ble_service: VeDbusService = None
        self._cont_scan_sync: VeDbusSettingItemSynchronizer = None
        self._settings_device: SettingsDevice = None
        
        self._adapters = []
        self._devices = {}

        # Initialize dbus service
        self.connect_dbus()
        self.ble_dbus_init()

        # Initialze BT adapters search
        self._list_adapters()

    def connect_dbus(self):
        self._bus = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

        # List services
        dbus_iface_names = dbus.Interface(
            self._bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus'),
            'org.freedesktop.DBus'
        ).ListNames()

        # Check settings service exists
        if self._SETTINGS_SERVICENAME not in dbus_iface_names:
            logging.error(f"DBus service {self._SETTINGS_SERVICENAME} does not exists. Can not continue.")
            sys.exit(1)

        # Check and create ble service
        if self._BLE_SERVICENAME in dbus_iface_names:
            logging.error(f"DBus service {self._BLE_SERVICENAME} is already running. Please stop it first.")
            sys.exit(1)
        logging.info("Creating dbus ble service")
        self._ble_service = VeDbusService(self._BLE_SERVICENAME, self._bus, False)
        self._ble_service.register()

        # Init settings access class
        self._settings_device = SettingsDevice(self._bus, {}, None)

    def ble_dbus_init(self):
        logging.info("Creating continuous scanning setting")
        setting_value = VeDbusItemImport(self._bus, self._SETTINGS_SERVICENAME, self._SETTINGS_CONTSCAN_PATH).get_value() or 0
        self._ble_service.add_path(self._BLE_CONTSCAN_PATH, setting_value, writeable=True)
        self._cont_scan_sync = VeDbusSettingItemSynchronizer(
            self._bus,
            get_setting_bool_property(self._SETTINGS_CONTSCAN_PATH, setting_value),
            self._ble_service,
            self._BLE_CONTSCAN_PATH
        )


    def _list_adapters(self):
        logging.debug("Listing hci devices")

        # Adding callback for futur connections/disconnections
        self._bus.add_signal_receiver(
            self._on_interfaces_added,
            dbus_interface='org.freedesktop.DBus.ObjectManager',
            signal_name='InterfacesAdded'
        )
        self._bus.add_signal_receiver(
            self._on_interfaces_removed,
            dbus_interface='org.freedesktop.DBus.ObjectManager',
            signal_name='InterfacesRemoved'
        )

        # Initial search for adapters
        object_manager = dbus.Interface(
            self._bus.get_object('org.bluez', '/'),
            'org.freedesktop.DBus.ObjectManager'
        )
        objects = object_manager.GetManagedObjects()
        for path, ifaces in objects.items():
            self._on_interfaces_added(path, ifaces)

    def _on_interfaces_added(self, path, interfaces):
        if not str(path).startswith('/org/bluez'):
            return
        logging.debug(f"Interfaces added: {path}, {interfaces}")
        if 'org.bluez.Adapter1' in interfaces:
            adapter = self._bus.get_object('org.bluez', path)
            props = dbus.Interface(adapter, 'org.freedesktop.DBus.Properties')
            mac = props.Get('org.bluez.Adapter1', 'Address')
            name = path.split('/')[-1]
            # Saving adapter
            if name == 'hci1':
                logging.info(f"Skipping adapter {name}")
                return
            logging.info(f"Adding adapter {name} found at {path} with address: {mac}")
            self._adapters.append(name)
            self._ble_service.add_path(f"/Interfaces/{name}/Address", mac, writeable=False)

    def _on_interfaces_removed(self, path, interfaces):
        if not str(path).startswith('/org/bluez'):
            return
        logging.debug(f"Interfaces removed: {path}, {interfaces}")
        if 'org.bluez.Adapter1' in interfaces:
            # Remove adapter
            name = path.split('/')[-1]
            logging.info(f"Adapter removed at {path}")
            self._adapters.remove(name)
            del self._dbus_ble_service[f"/Interfaces/{name}/Address"]


    def get_cont_scan(self) -> bool:
        return bool(self._ble_service[_BLE_CONTSCAN_PATH])


    def _init_dev(self, dev: str, info: BleDevices, data: dict):
        droot = {}
        droot['id'] = dev
        droot['info'] = info
        droot['data'] = data
        droot['dev_id'] = droot['info'].dev_prefix + dev
        droot['settings_path'] = f"/Settings/Devices/{droot['dev_id']}"
        self._devices[dev] = droot
        return droot

    def ble_dbus_is_enabled(droot: dict) -> int:
        return self._ble_service[f"Devices/{droot['dev_id']}/Enabled"]

    def ble_dbus_add_settings(self, droot: dict, settings: dict):
        for name, conf in settings.items():
            droot[name] = self._settings_device.addSetting(
                *get_setting_custom_property(
                    f"{droot['settings_path']}/{name}",
                    conf.get('def', 0), 
                    conf.get('min', 0), 
                    conf.get('max', 0)
                )
            )
            # TODO: handle onchange callbacks

    def ble_dbus_add_alarms(self, droot: dict, alarms: dict):
        path = droot['settings_path']
        for name, conf in alarms.items():
            if conf.contains("ALARM_FLAG_CONFIG"):
                buf = f"Alarms/{name}/Enable"
                droot[buf] = self._settings_device.addSetting(*get_setting_bool_property(f"{path}/{buf}"))
                buf = f"Alarms/{name}/Active"
                droot[buf] = self._settings_device.addSetting(*get_setting_int_property(f"{path}/{buf}", conf['active'].get('def', 80), conf['active'].get('min', 0), conf['active'].get('max', 0)))
                buf = f"Alarms/{name}/Restore"
                droot[buf] = self._settings_device.addSetting(*get_setting_bool_property(f"{path}/{buf}", conf['restore'].get('def', 80), conf['restore'].get('min', 0), conf['restore'].get('max', 0)))
    
    def ble_dbus_create(self, dev: str, info: BleDevices, data: dict) -> dict:
        logging.info(f"Creating {dev} device in dbus")

        if  dev in self._devices:
            logging.info(f"Device {dev} already exists in dbus, skipping creation")
            droot =  self._devices[dev]
            droot['tick'] = 0
            return droot

        droot = self._init_dev(dev, info, data)

        # Init Enabled setting
        path = droot['settings_path']
        name = f"/Devices/{droot['dev_id']}/Enabled"
        setting_value = VeDbusItemImport(self._bus, self._SETTINGS_SERVICENAME, f"{path}/Enabled").get_value() or 0
        logging.info(f"Adding device {droot['dev_id']} to dbus")
        self._ble_service.add_path(name, setting_value, writeable=True)
        self._device_enabled_sync = VeDbusSettingItemSynchronizer(
            self._bus,
            get_setting_bool_property(f"{path}/Enabled", setting_value),
            self._ble_service,
            item_path=name
        )
        # TODO handle callback to monitor Enabled on and off

        # Init CustomName setting
        droot['CustomName'] = self._settings_device.addSetting(*get_setting_str_property(f"{path}/CustomName"))

        # Init classes settings
        for clazz in droot['info'].classes:
            self.ble_dbus_add_settings(droot, clazz.settings)
            self.ble_dbus_add_alarms(droot, clazz.alarms)
            clazz.init(droot, data)

        # Init device settings
        self.ble_dbus_add_settings(droot, droot['info']settings)
        self.ble_dbus_add_alarms(droot, droot['info'].alarms)
        droot['info'].init(droot, data)

        droot['tick'] = 0
        return droot

    def ble_dbus_connect(self, droot: dict) -> int:

        if droot['dbus']:
            return 0

        if not droot['info']:
            return -1

        roles = []
        roles += droot['info'].role
        for clazz in droot['info'].classes:
            roles += clazz.role

        for role_index, role in enumerate(roles):
            dev_instance = veDbusGetVrmDeviceInstance(droot['dev_id'], role, droot['info'].dev_instance) #TODO implement
            if dev_instance < 0:
                return -1

            ble_dbus_set_str(droot, "Mgmt/ProcessName", pltProgramName()); #TODO implement
            ble_dbus_set_str(droot, "Mgmt/ProcessVersion", self._VERSION)
            ble_dbus_set_str(droot, "Mgmt/Connection", "Bluetooth LE")
            ble_dbus_set_int(droot, "Connected", 1)
            ble_dbus_set_int(droot, f"Devices/${role_index}/ProductId", droot['info']['product_id'])
            ble_dbus_set_int(droot, f"Devices/${role_index}/DeviceInstance", dev_instance)
            ble_dbus_set_int(droot, "DeviceInstance", dev_instance)
            ble_dbus_set_str(droot, "ProductName", veProductGetName(droot['info']['product_id']));
            ble_dbus_set_int(droot, "Status", 0);
            veItemCreateProductId(droot, droot['info']['product_id']);

            snprintf(name, sizeof(name), "com.victronenergy.%s.%s", role, droot['dev_id']);

            dbus = veDbusConnectString(veDbusGetDefaultConnectString());
            if (!dbus) {
                fprintf(stderr, "%s: dbus connection failed\n", dev);
                return -1;
            }

            veDbusItemInit(dbus, droot);
            veDbusChangeName(dbus, name);

        return 0

    def ble_dbus_set_regs(self, droot: dict, data: bytes):
        for reg in droot['info'].regs:
            val = None
            match reg.type:
                case dbus.types.Boolean:
                    val = bool(self.load_int(reg, droot, data))
                case dbus.types.Byte|dbus.types.Int16|dbus.types.UInt16|dbus.types.Int32|dbus.types.UInt32|dbus.types.Int64|dbus.types.UInt64:
                    val = self.load_int(reg, droot, data)
                case dbus.types.Double:
                    pass
                case dbus.types.String:
                    pass
                case dbus.types.ObjectPath|dbus.types.Signature|dbus.types.Array|dbus.types.Dictionary|dbus.types.ByteArray|dbus.types.Variant:
                    pass
                case _:
                    pass
                
            if val is None:
                continue
            droot[reg.name] = (reg.format) val

    def type_size(self, type) -> int:
        match reg.type:
            case dbus.types.Boolean|dbus.types.Byte:
                return 8
            case dbus.types.Int16|dbus.types.UInt16:
                return 16
            case dbus.types.Int32|dbus.types.UInt32:
                return 32
            case dbus.types.Int64|dbus.types.UInt64:
                return 64
            case _:
                return None

    def type_issigned(self, type) -> Boolean:
        return True if _SIGNED_TYPES.contains(type) else False

    def load_int(self, reg: dict, droot: dict, data: bytes):
        offset: int = reg.offset
        flags: list = reg.flags or []
        shift: int = reg.shift
        
        # Get data length
        bits = reg.bits or 0
        if bits == 0:
            bits = self.type_size(reg.type)
        if bits is None:
            return None

        # Check there is enough data for the expected value
        size = (bits + shift + 7) >> 3
        if size > len(data) - offset
            return None

        # Read data
        value = int.from_bytes(
            data[offset:offset + size], 
            'big' if flags.contains("REG_FLAG_BIG_ENDIAN") else 'little', 
            self.type_issigned(reg.type)
        )

        # Applying shift and triming on bits size
        value = (value >> shift) << 64 - bits >> 64 - bits

        # Post actions
        if flags.contains("REG_FLAG_INVALID") and value == reg.inval:
            return None
        elif reg.xlate:
            return getattr(self, reg.xlate)(droot, value)
        elif reg.scale:
            return value / reg.scale + (reg.bias or 0)
        else:
            return value

    def ble_dbus_set_item(self, root: dict, path:str, value) -> int:
        item = self._ble_service.add_path(path, value, writeable=False)
        return -1 if not item else 0

    def ble_dbus_set_str(self, root: dict, path:str, string:str) -> int:
        return ble_dbus_set_item(root, path, string, &veUnitNone)

    def ble_dbus_set_int(self, root: dict, path:str, num:int) -> int:
        return ble_dbus_set_item(root, path, num, &veUnitNone)

    def ble_dbus_set_name(self, droot: dict, name: str):
        droot['DeviceName'] = name
        self._ble_service.add_path(
            f"Devices/{droot['dev_id']}/Name",
            droot['CustomName'] or name,
            writeable=True
        )

    def alarm_name(self, alarm: dict) -> str:
        if "ALARM_FLAG_CONFIG" in alarm.flags:
            return f"Alarms/{alarm.name}/State"
        return f"Alarms/{alarm.name}"

    def alarm_enabled(self, droot: dict, alarm: dict) -> bool :
        if "ALARM_FLAG_CONFIG" in alarm.flags:
            enable = f"Alarms/{alarm.name}/Enable"
            return bool(droot[enable])
        return True

    def alarm_level(self, droot: dict, alarm: dict, active: bool) -> float :
        if "ALARM_FLAG_CONFIG" in alarm.flags:
            level_name = f"Alarms/{alarm.name}/{"Restore" if active else "Active"}"
            return droot[level_name]

        level = alarm.get_level(droot, alarm) if alarm.get_level else level = alarm.level
        if active:
            level += alarm.hyst or 0
        return level

    def update_alarm(self, droot: dict, alarm: dict):
        if not self.alarm_enabled(droot, alarm):
            return

        alarm_name = self.alarm_name(alarm)
        active = bool(droot[alarm_name]) or False

        level = self.alarm_level(droot, alarm, active)
        item = float(droot[alarm.item])
        droot[alarm_name] = item > level if "ALARM_FLAG_HIGH" in alarm.flags else item < level

    def ble_dbus_update_alarms(self, droot: dict):
        for clazz in droot['info'].classes:
            for alarm in clazz.alarms:
                self.update_alarm(droot, alarm)

        for alarm in droot['info'].alarms:
            self.update_alarm(droot, alarm)

    def ble_dbus_update(self, droot: dict):
        for clazz in droot['info'].classes:
            clazz.update(droot, data)

        self.ble_dbus_update_alarms(droot)
        self.ble_dbus_connect(droot) #TODO implement
        veItemSendPendingChanges(droot)

