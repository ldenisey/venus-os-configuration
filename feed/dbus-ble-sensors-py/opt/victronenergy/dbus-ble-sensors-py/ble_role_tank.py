from ble_role import BleRole


class BleRoleTank(BleRole):

    FLUID_TYPES = {
        0: 'Fuel',
        1: 'Fresh water',
        2: 'Waste water',
        3: 'Live well',
        4: 'Oil',
        5: 'Black water (sewage)',
        6: 'Gasoline',
        7: 'Diesel',
        8: 'LPG',
        9: 'LNG',
        10: 'Hydraulic oil',
        11: 'Raw water'
    }

    def __init__(self):
        super().__init__()

        self.info.update(
            {
                "name": "tank",
                'settings': [
                    {
                        'name': 'Capacity',
                        'props': {
                            'def': 0.2,
                            'min': 0,
                            'max': 1000
                        },
                        'onchange': self.setting_changed
                    },
                    {
                        'name': 'FluidType',
                        'props': {
                            'def': 0,
                            'min': 0,
                            'max': 2**31 - 4  # (INT32_MAX - 3)
                        }
                    },
                    {
                        'name': 'Shape',
                        'props': {
                            'def': '',
                            'min': 0,
                            'max': 0
                        },
                        'onchange': self.shape_changed
                    },
                ],
                'alarms': [
                    {
                        'name': 'High',
                        'item': 'Level',
                        'flags': ['ALARM_FLAG_HIGH', 'ALARM_FLAG_CONFIG'],
                        'active': {
                            'def': 90,
                            'min': 0,
                            'max': 100
                        },
                        'restore': {
                            'def': 80,
                            'min': 0,
                            'max': 100
                        },
                    },
                    {
                        'name': 'Low',
                        'item': 'Level',
                        'flags': ['ALARM_FLAG_CONFIG'],
                        'active': {
                            'def': 10,
                            'min': 0,
                            'max': 100
                        },
                        'restore': {
                            'def': 15,
                            'min': 0,
                            'max': 100
                        },
                    },
                ],
            }
        )

    def setting_changed(self, device_info: dict, data: dict):
        raise NotImplementedError("To be implemented")

    def shape_changed(self, device_info: dict, data: dict):
        raise NotImplementedError("To be implemented")
