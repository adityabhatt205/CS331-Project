class LogManager:
    def __init__(self):
        self._logs = []

    def storeLog(self, log) -> None:
        self._logs.append(log)

    def retrieveLogs(self):
        return self._logs

    def encryptLog(self, log) -> None:
        pass
