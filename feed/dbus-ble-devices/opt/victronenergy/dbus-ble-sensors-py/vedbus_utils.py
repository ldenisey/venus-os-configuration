import dbus
import logging
import sys
import os

# Import Victron Energy's python library.
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from vedbus import VeDbusItemImport, VeDbusService
from settingsdevice import SettingsDevice

class VeDbusItemsSynchronizer:
    """
    Provides 2-way synchronization between two dbus node items.
    """

    _item1_service: VeDbusService = None
    _item1: VeDbusItemImport = None
    item1_service_name: str = None
    item1_path: str = None

    _item2_service: VeDbusService = None
    _item2: VeDbusItemImport = None
    item2_service_name: str = None
    item2_path: str = None


    def __init__(self, bus, item1, item2, item1_path: str = None, item2_path: str = None):
        """
        Both path must exists in their respective services.
        @param item1, item2: Service name as string, item as VeDbusItemImport or service as VeDbusService object.
        @param item1_path, item2_path: Target path, when item1/item2 is of type string or VeDbusService. Ignored when type is VeDbusItemImport.
        """
        match item1:
            case str():
                if item1_path is None:
                    logging.error("item1_path is mandatory with item1 is given as a string.")
                    raise ValueError("item1_path is mandatory with item1 is given as a string.")
                self.item1_service_name = item1
                self.item1_path = item1_path
                self._item1 = VeDbusItemImport(bus, self.item1_service_name, self.item1_path, eventCallback=self._item1_valueChangedCallback)
            case VeDbusItemImport():
                self.item1_service_name = item1.serviceName
                self.item1_path = item1.path
                self._item1 = VeDbusItemImport(bus, self.item1_service_name, self.item1_path, eventCallback=self._item1_valueChangedCallback)
            case VeDbusService():
                if item1_path is None:
                    logging.error("item1_path is mandatory with item1 is given as a VeDbusService.")
                    raise ValueError("item1_path is mandatory with item1 is given as a VeDbusService.")
                self.item1_service_name = item1.get_name()
                self.item1_path = item1_path
                self._item1_service = item1
                self._item1_service._onchangecallbacks[self.item1_path] = self._item1_onchangecallback
            case _:
                logging.error(f"Unsupported type for item1: {type(item1)}")

        match item2:
            case str():
                if item2_path is None:
                    logging.error("item2_path is mandatory with item2 is given as a string.")
                    raise ValueError("item2_path is mandatory with item2 is given as a string.")
                self.item2_service_name = item2
                self.item2_path = item2_path
                self._item2 = VeDbusItemImport(bus, self.item2_service_name, self.item2_path, eventCallback=self._item2_valueChangedCallback)
            case VeDbusItemImport():
                self.item2_service_name = item2.serviceName
                self.item2_path = item2.path
                self._item2 = VeDbusItemImport(bus, self.item2_service_name, self.item2_path, eventCallback=self._item2_valueChangedCallback)
            case VeDbusService():
                if item2_path is None:
                    logging.error("item2_path is mandatory with item2 is given as a VeDbusService.")
                    raise ValueError("item2_path is mandatory with item2 is given as a VeDbusService.")
                self.item2_service_name = item2.get_name()
                self.item2_path = item2_path
                self._item2_service = item2
                self._item2_service._onchangecallbacks[self.item2_path] = self._item2_onchangecallback
            case _:
                logging.error(f"Unsupported type for item2: {type(item2)}")

        logging.info(f"{self} initialized")
    

    def _get_item_value(self, item: VeDbusItemImport, item_service: VeDbusService, item_path: str):
        if item is not None:
            return item.get_value()
        elif item_service is not None:
            return item_service[item_path]
        else:
            raise ValueError("Initialization error")

    def get_item1_value(self):
        try:
            self._get_item_value(self._item1, self._item1_service, self.item1_path)
        except ValueError as ve:
            logging.error(f"Error getting item1 value: {ve}")
            return None

    def get_item2_value(self):
        try:
            self._get_item_value(self._item2, self._item2_service, self.item2_path)
        except ValueError as ve:
            logging.error(f"Error getting item2 value: {ve}")
            return None

    def _set_item_value(self, item: VeDbusItemImport, item_service: VeDbusService, item_path: str, value: str):
        if item is not None:
            return item.set_value(value)
        elif item_service is not None:
            return item_service.__setitem__(item_path, value)
        else:
            raise ValueError("Initialization error")

    def set_item1_value(self, value: str):
        try:
            self._set_item_value(self._item1, self._item1_service, self.item1_path, value)
        except ValueError as ve:
            logging.error(f"Error setting item1 value: {ve}")
            return None

    def set_item2_value(self, value: str):
        try:
            self._set_item_value(self._item2, self._item2_service, self.item2_path, value)
        except ValueError as ve:
            logging.error(f"Error setting item2 value: {ve}")
            return None


    def _item_changecallback(self, service_name: str, path: str, new_value) -> bool:
        # Target is the other one
        if service_name == self.item1_service_name:
            target_service_name = self.item2_service_name
            target_path = self.item2_path
            target_value = self.get_item2_value()
            target_set = self.set_item2_value
        elif service_name == self.item2_service_name:
            target_service_name = self.item1_service_name
            target_path = self.item1_path
            target_value = self.get_item2_value()
            target_set = self.set_item1_value
        else:
            logging.error(f"Received an unexpected update: {service_name}@{path}: {new_value}")
            return False
        
        if target_value != new_value or type(target_value) != type(new_value):
            logging.info(f"Updating {target_service_name} {target_path} to {new_value}")
            target_set(new_value)
        return True

    def _item1_valueChangedCallback(self, service_name, path, changes):
        logging.info(f"Received update on {service_name} {path}: {changes}")
        if service_name != self.item1_service_name or path != self.item1_path:
            return False
        return self._item_changecallback(service_name, path, changes['Value'])
    
    def _item1_onchangecallback(self, path, newvalue):
        logging.info(f"Received update on {path}: {newvalue}")
        if path != self.item1_path:
            return False
        return self._item_changecallback(self.item1_service_name, path, newvalue)

    def _item2_valueChangedCallback(self, service_name, path, changes):
        logging.info(f"Received update on {service_name} {path}: {changes}")
        if service_name != self.item2_service_name or path != self.item2_path:
            return False
        return self._item_changecallback(service_name, path, changes['Value'])
    
    def _item2_onchangecallback(self, path, newvalue):
        logging.info(f"Received update on {path}: {newvalue}")
        if path != self.item2_path:
            return False
        return self._item_changecallback(self.item2_service_name, path, newvalue)

    def __str__(self):
        return f"VeDbusItemsSynchronizer({self.item1_service_name}@{self.item1_path} <-> {self.item2_service_name}@{self.item2_path})"

def get_setting_custom_property(path: str, value, min = 0, max = 0, silent: bool = False) -> list:
    """
    @param path: Full setting path, e.g. /Settings/Some/Path
    @param value: Default value for the setting
    @param min: Minimum value for numbers else 0
    @param max: Maximum value for numbers else 0
    @param silent: Whether to log changes or not
    """
    return [path, value, min, max, silent]

def get_setting_str_property(path: str, value: str = "", silent: bool = False) -> list:
    return get_setting_custom_property(path, value, silent=silent)

def get_setting_bool_property(path: str, value: bool = False, silent: bool = False) -> list:
    return get_setting_custom_property(path, 1 if value else 0, 0, 1, silent)

def get_setting_int_property(path: str, value: int, min: int, max: int, silent: bool = False) -> list:
    return get_setting_custom_property(path, value, min, max, silent)

def get_setting_float_property(path: str, value: float, min: float, max: float, silent: bool = False) -> list:
    return get_setting_custom_property(path, value, min, max, silent)


class VeDbusSettingItemSynchronizer(VeDbusItemsSynchronizer):
    """
    Provides 2-way synchronization between a victron setting and a dbus node item.
    See https://github.com/victronenergy/localsettings for more information on settings.
    """

    def __init__(self, bus, setting_property: list, item, item_path: str = None):
        """
        @param setting_property: A list defining the property. Use get_setting_custom_property method or similar to create one. Will create or update the setting if needed.
        @param item: Service name as string, item as VeDbusItemImport or service as VeDbusService object.
        @param item_path: Target path, when item is of type string or VeDbusService. Ignored when type is VeDbusItemImport.
        """
        settings_device = SettingsDevice(bus, {}, None)
        setting_item = settings_device.addSetting(*setting_property, None)
        super().__init__(bus, setting_item, item, item2_path=item_path)








