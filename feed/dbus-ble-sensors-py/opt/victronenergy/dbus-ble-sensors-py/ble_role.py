import os
import sys
import inspect
import logging
import importlib.util


class BleRole(object):

    _ROLE_INSTANCE = {}

    def __init__(self):
        self.info = {
            "name": None,    # Mandatory, str, role name
            'settings': [],  # Optional, list of dict, settings that could be set through UI
            'alarms': [],    # Optional, list of dict, possible alarms raised by the device
        }

    def init(self, ble_device):
        """
        Optional method executed during configuration, when the first advertising of this device has been detected.
        """
        self._plog = f"{self.info['name']} :"

    def update(self, ble_device, values: dict):
        """
        Optional method executed at advertising reception, after the data have been parsed to update values and settings.
        """
        pass

# /!\/!\/!\/!\/!\/!\  Methods below should not been overrided  /!\/!\/!\/!\/!\/!\

    @staticmethod
    def get_role_instance(role_name: str):
        return BleRole._ROLE_INSTANCE.get(role_name, None)

    @staticmethod
    def load_role_classes(execution_path: str):
        logging.debug("Role classes: loading...")
        role_classes_prefix = f"{os.path.splitext(os.path.basename(__file__))[0]}_"

        # Loading manufacturer specific classes
        for filename in os.listdir(os.path.dirname(execution_path)):
            if filename.startswith(role_classes_prefix) and filename.endswith('.py'):
                module_name = os.path.splitext(filename)[0]

                # Import the module from file
                logging.debug(f"Role classes: loading module {module_name} ...")
                spec = importlib.util.spec_from_file_location(module_name, filename)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logging.debug(f"Role classes: module {module_name} loaded")

                # Check and import
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__ == module.__name__ and issubclass(obj, BleRole) and obj is not BleRole:
                        instance = obj()
                        instance.check_configuration()
                        BleRole._ROLE_INSTANCE[instance.info['name']] = instance
                        break
                logging.debug(f"Role classes: class {module_name} instanciated")
        logging.info(f"Role classes: {BleRole._ROLE_INSTANCE}")

    def check_configuration(self):
        for key in ['name', 'settings', 'alarms']:
            if key not in self.info:
                raise ValueError(f"{self._plog} configuration '{key}' is missing")
            if self.info[key] is None:
                raise ValueError(f"{self._plog} Configuration '{key}' can not be None")

        for list_key in ['settings', 'alarms']:
            if not isinstance(self.info[list_key], list):
                raise ValueError(f"{self._plog} Configuration '{list_key}' must be a list")

        for index, setting in enumerate(self.info['settings']):
            if 'name' not in setting:
                raise ValueError(f"{self._plog} Missing 'name' in setting at index {index}")
            if 'props' not in setting:
                raise ValueError(f"{self._plog} Missing 'props' definition in setting {setting['name']}")
            for key in ['def', 'min', 'max']:
                if key not in setting['props']:
                    raise ValueError(f"{self._plog} Missing key '{key}' in setting {setting['name']}")

        for index, alarm in enumerate(self.info['alarms']):
            if 'name' not in alarm:
                raise ValueError(f"{self._plog} Missing 'name' in alarm at index {index}")
            for key in ['item', 'active', 'restore']:
                if key not in alarm:
                    raise ValueError(f"{self._plog} Missing key '{key}' in alarm {alarm['name']}")
            for sig in ['active', 'restore']:
                for key in ['def', 'min', 'max']:
                    if key not in alarm[sig]:
                        raise ValueError(f"{self._plog} Missing key '{key}' in field {sig} of alarm {alarm['name']}")
            if (alarm.get('flags', None) and 'ALARM_FLAG_CONFIG' not in alarm['flags']) and alarm.get('level', None) is None and alarm.get('getlevel', None) is None:
                raise ValueError(
                    f"{self._plog} Alarm {alarm['name']}must define a level with a 'level' or a 'getlevel' fields or using dbus configuration with 'ALARM_FLAG_CONFIG' flag.")

    def get_name(self):
        return self.info['name']
