class SensorNetwork:
    def __init__(self):
        self._sensors = []

    def collectSensorData(self) -> None:
        for sensor in self._sensors:
            sensor.readData()
