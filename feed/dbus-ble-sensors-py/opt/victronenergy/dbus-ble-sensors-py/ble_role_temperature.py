from ble_role import BleRole


class BleRoleTemperature(BleRole):

    TEMPERATURE_TYPES = {
        0: 'Battery',
        1: 'Fridge',
        2: 'Generic',
        3: 'Room',
        4: 'Outdoor',
        5: 'WaterHeater',
        6: 'Freezer'
    }

    def __init__(self):
        super().__init__()

        self.info.update(
            {
                "name": "temperature",
                'settings': [
                    {
                        'name': 'TemperatureType',
                        'props': {
                            'def': 2,
                            'min': 0,
                            'max': 6
                        }
                    }
                ],
            }
        )
