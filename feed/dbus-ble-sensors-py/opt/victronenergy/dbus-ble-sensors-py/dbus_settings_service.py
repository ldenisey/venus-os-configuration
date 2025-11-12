from __future__ import annotations
import os
import sys
import dbus
import logging

# Import Victron Energy's python library.
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from vedbus import VeDbusItemImport


class DbusSettingsService(object):
    # Inspired from SettingsDevice class of settingsdevice.py file of velib_python, but :
    # - removing the use of arbitrary setting names, using paths instead
    # - allowing reading settings
    # - allowing different callbacks for each settings

    _SETTINGS_SERVICENAME = 'com.victronenergy.settings'
    _INSTANCE: DbusSettingsService = None

    def __init__(self):
        DbusSettingsService._INSTANCE = self
        self._bus: dbus.Bus = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()
        self._paths = {}

        # Check settings service exists
        if self._SETTINGS_SERVICENAME not in self._bus.list_names():
            raise Exception(f"Dbus service {self._SETTINGS_SERVICENAME} does not exist.")

    @staticmethod
    def get() -> DbusSettingsService:
        return DbusSettingsService._INSTANCE

    def get_item(self, path: str, def_value: any = None, min_value: int = 0, max_value: int = 0) -> VeDbusItemImport:
        # Get the setting item, initializing it only if it does not exists and if a default value is given
        if (item := self._paths.get(path, None)) is None:
            item = VeDbusItemImport(self._bus, self._SETTINGS_SERVICENAME, path)
            if not item.exists and def_value is not None:
                item = self.set_item(path, def_value, def_value, max_value)
            self._paths[path] = item
        return item

    def get_value(self, path) -> any:
        return self.get_item(path).get_value()

    def set_item(self, path: str, def_value: any = None, min_value: int = 0, max_value: int = 0, silent=False, callback=None) -> VeDbusItemImport:
        busitem = VeDbusItemImport(self._bus, self._SETTINGS_SERVICENAME, path, callback)
        if not busitem.exists or (def_value, min_value, max_value, silent) == busitem._proxy.GetAttributes():
            # Get value type
            if isinstance(def_value, (int, dbus.Int64)):
                itemType = 'i'
            elif isinstance(def_value, float):
                itemType = 'f'
            else:
                itemType = 's'

            # Add the setting
            setting_item = VeDbusItemImport(self._bus, self._SETTINGS_SERVICENAME, '/Settings', createsignal=False)
            setting_path = path.replace('/Settings/', '', 1)
            if silent:
                setting_item._proxy.AddSilentSetting('', setting_path, def_value, itemType, min_value, max_value)
            else:
                setting_item._proxy.AddSetting('', setting_path, def_value, itemType, min_value, max_value)

            # Get the setting as a victron bus item
            busitem = VeDbusItemImport(self._bus, self._SETTINGS_SERVICENAME, path, callback)

        self._paths[path] = busitem
        return busitem

    def set_value(self, path, new_value):
        if (setting := self._paths.get(path, None)) is None:
            logging.warning(f"Can not set value of unexisting {path} to {new_value}.")
        else:
            if (result := setting.set_value(new_value)) != 0:
                logging.warning(f"Failed to set setting {path} to {new_value}.")

    def set_event_callback(self, path, callback):
        item = self.get_item(path)
        # Concatenate callback if needed
        if (existing_callback := item.eventCallback) is not None:
            item.eventCallback = lambda service_name, change_path, changes: (existing_callback(
                service_name, change_path, changes), callback(service_name, change_path, changes))
        else:
            item.eventCallback = callback

    def set_proxy_callback(self, setting_path: str, remote_item: VeDbusItemImport):
        def _callback(service_name, change_path, changes):
            logging.debug(f"Received update on {service_name}@{change_path}: {changes}")
            if service_name != DbusSettingsService._SETTINGS_SERVICENAME or change_path != setting_path:
                return
            new_value = changes['Value']
            if new_value != remote_item.get_value():
                logging.debug(f"Updating {remote_item.serviceName}@{remote_item.path} to {new_value}")
                remote_item.set_value(new_value)
        self.set_event_callback(setting_path, _callback)

    def __getitem__(self, path):
        return self.get_value(path)

    def __setitem__(self, path, new_value):
        self.set_value(path, new_value)

    def get_custom_name(self, device_info: dict) -> str:
        item = self.get_item(f"/Settings/Devices/{device_info['dev_id']}/CustomName")
        return item.get_value() if item.exists else None
