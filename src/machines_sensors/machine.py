class Machine:
    def __init__(self, machine_id: int):
        self._machine_id = machine_id
        self._status = "IDLE"

    def start(self) -> None:
        self._status = "RUNNING"

    def stop(self) -> None:
        self._status = "STOPPED"

    def adjustSpeed(self, value: int) -> None:
        print(f"Adjusting speed to {value}")

    def validateCommand(self, cmd: str) -> bool:
        return True
