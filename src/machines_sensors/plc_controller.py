class PLCController:
    def sendControlCommand(self, cmd: str) -> None:
        print(f"Sending PLC command: {cmd}")

    def readMachineStatus(self) -> str:
        return "RUNNING"

    def authenticateCommand(self, cmd: str) -> bool:
        return True
