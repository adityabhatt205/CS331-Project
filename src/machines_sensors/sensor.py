class Sensor:
    def __init__(self, sensor_id: int, sensor_type: str):
        self._sensor_id = sensor_id
        self._type = sensor_type
        self._value = 0.0

    def readData(self) -> float:
        return self._value
