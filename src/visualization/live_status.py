class LiveStatus:
    def __init__(self, temperature: float, speed: float, machine_state: str):
        self._temperature = temperature
        self._speed = speed
        self._machine_state = machine_state

    def updateStatus(self, temperature: float, speed: float, state: str) -> None:
        self._temperature = temperature
        self._speed = speed
        self._machine_state = state
