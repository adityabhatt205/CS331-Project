from datetime import datetime

class Log:
    def __init__(self, log_id: int, message: str):
        self._log_id = log_id
        self._timestamp = datetime.now()
        self._message = message
