import os
import sys
import logging
import dbus
from dbus_settings_service import DbusSettingsService
from ble_role import BleRole

# Import Victron Energy's python library.
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from vedbus import VeDbusService, VeDbusItemImport


class DbusDeviceService(object):

    def __init__(self, ble_device, ble_role: BleRole):
        # private=True to allow creation of multiple services in the same app
        self._bus: dbus.Bus = dbus.SessionBus(
            private=True) if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus(private=True)
        self._ble_device = ble_device
        self.ble_role = ble_role
        self._dbus_service: VeDbusService = None  # Is velib_python good enough to be a parent class ?
        self._service_name: str = None
        self._device_instance: int = None
        self._dbus_iface = dbus.Interface(
            self._bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus'),
            'org.freedesktop.DBus')
        self._dev_id = self._ble_device.info['dev_id']
        self.init_service()

    def is_connected(self) -> bool:
        # Local check
        if self._dbus_service is None:
            return False

        # Dbus check
        return self._dbus_iface.NameHasOwner(self._service_name)

    def get_vrm_device_instance(self) -> int:
        # TODO understand how dev_id is used in c library function
        # Load devices from settings
        devices_string: dict = DbusSettingsService.get().get_item('/Settings/Devices').get_value()
        if not devices_string:
            return -1

        # Get existing ClassAndVrmInstance anf filter them by role
        role_name = self.ble_role.get_name()
        existing_instances = []
        for key, value in devices_string.items():
            if 'ClassAndVrmInstance' in key and value.startswith(role_name):
                existing_instances.append(value)

        # Increment instance until free one found
        cur_instance = int(self._ble_device.info['dev_instance'])
        while f"{role_name}:{cur_instance}" in existing_instances:
            cur_instance += 1
        return cur_instance

    def init_service(self):
        self._service_name = f"com.victronenergy.{self.ble_role.info['name']}.{self._dev_id}"
        self._device_instance = self.get_vrm_device_instance()
        if self._device_instance < 0:
            raise ValueError(
                f"Can not get dev_instance for device {self._ble_device.info['DeviceName']} and role {self.ble_role.get_name()}")

        logging.debug(f"Initializing dbus '{self._service_name}'")
        self._dbus_service = VeDbusService(self._service_name, self._bus, False)

        self._dbus_service.add_mandatory_paths(
            os.environ["PROCESS_NAME"],
            os.environ["PROCESS_VERSION"],
            "Bluetooth LE",
            self._device_instance,
            self._ble_device.info['product_id'],
            self._ble_device.info['product_name'],
            self._ble_device.info['firmware_version'],
            self._ble_device.info['hardware_version'],
            1
        )
        self._dbus_service.add_path("/Devices/0/ProductId",
                                    self._ble_device.info['product_id'], writeable=False)  # Is this needed ?
        self._dbus_service.add_path("/Devices/0/DeviceInstance", self._device_instance,
                                    writeable=False)  # Is this needed ?
        self._dbus_service.add_path("/Status", 0, writeable=True)
        # veItemCreateProductId(droot, self._ble_device.info['product_id']);  #TODO Does it do more than adding a product_id item ?

    def connect(self):
        if self.is_connected():
            return
        logging.info(f"Registrating dbus '{self._service_name}' service on bus {self._bus}")
        self._dbus_service.register()

    def disconnect(self):
        if not self.is_connected():
            return
        logging.warning(f"Releasing device '{self._ble_device.info['DeviceName']}' dbus service")
        self._dbus_service._dbusname.release()

    def _clear_path(self, path: str) -> str:
        return f"/{path.lstrip('/').rstrip('/')}"

    def get_value(self, path: str) -> any:
        return self._dbus_service._dbusobjects.get(self._clear_path(path), None)

    def set_value(self, path: str, value: any):
        clean_path = self._clear_path(path)
        if (item := self._dbus_service._dbusobjects.get(clean_path, None)) is None:
            self._dbus_service.add_path(clean_path, value)
        else:
            self._dbus_service[clean_path] = value

    def _get_proxy_callback(self, item_path: str, setting_item: VeDbusItemImport, callback=None) -> any:
        def _callback(path: str, new_value: any):
            logging.debug(f"Received update on {self._service_name}@{path}: {new_value}")
            if path != item_path:
                return
            if new_value != setting_item.get_value():
                logging.debug(f"Updating {setting_item.serviceName}@{setting_item.path} to {new_value}")
                setting_item.set_value(new_value)
            if callback:
                callback(new_value)
        return _callback

    def _init_proxy_setting(self, setting_path: str, item_path: str, default_value: any, min_value: int = 0, max_value: int = 0, callback=None):
        # Get or set setting
        setting_item = DbusSettingsService.get().get_item(setting_path, default_value, min_value, max_value)

        # Init item and custom callback
        item = self._dbus_service.add_path(
            item_path,
            setting_item.get_value(),
            onchangecallback=self._get_proxy_callback(item_path, setting_item, callback)
        )

        # Set settings callback
        setting_item = DbusSettingsService.get().set_proxy_callback(setting_path, item)

    def init_custom_name(self):
        self._init_proxy_setting(
            f"/Settings/Devices/{self._dev_id}/CustomName",
            '/CustomName',
            '',
        )

    def add_setting(self, setting: dict):
        name = self._clear_path(setting['name'])
        props = setting['props']
        self._init_proxy_setting(
            f"/Settings/Devices/{self._dev_id}{name}",
            name,
            props['def'],
            props['min'],
            props['max']
        )

    def add_alarm(self, alarm: dict):
        name = alarm['name']
        self._init_proxy_setting(
            f"/Settings/Devices/{self._dev_id}/Alarms/{name}/Enable",
            f"/Alarms/{name}/Enable",
            0,
            0,
            1
        )
        self._init_proxy_setting(
            f"/Settings/Devices/{self._dev_id}/Alarms/{name}/Active",
            f"/Alarms/{name}/Active",
            alarm['active']['def'],
            alarm['active']['min'],
            alarm['active']['max']
        )
        self._init_proxy_setting(
            f"/Settings/Devices/{self._dev_id}/Alarms/{name}/Restore",
            f"/Alarms/{name}/Restore",
            alarm['restore']['def'],
            alarm['restore']['min'],
            alarm['restore']['max']
        )

    def is_alarm_enabled(self, alarm: dict) -> bool:
        alarm_enable = True
        if 'ALARM_FLAG_CONFIG' in alarm['flags']:
            alarm_enable = bool(self._debus_service[f"/Alarms/{alarm['name']}/Enable"])
        return alarm_enable

    def _get_alarm_active_status_path(self, alarm: dict) -> str:
        state_path = f"/Alarms/{alarm['name']}"
        if 'ALARM_FLAG_CONFIG' in alarm['flags']:
            state_path = state_path + '/State'
        return state_path

    def get_alarm_active_status(self, alarm: dict) -> bool:
        active: bool = False
        state_path = self._get_alarm_active_status_path(alarm)

        # TODO understand who, where and when this is created and check if it is a bool or an int
        if self._dbus_service._dbusobjects.get(state_path, None) is not None:
            active = bool(self._dbus_service[state_path])

        return active

    def set_alarm_active_status(self, alarm: dict, active: bool):
        state_path = self._get_alarm_active_status_path(alarm)
        self._dbus_service[state_path] = active

    def get_alarm_level(self, alarm: dict, active: bool) -> any:
        level_name = f"/Alarms/{alarm['name']}/{"Restore" if active else "Active"}"
        return self._dbus_service[level_name]
