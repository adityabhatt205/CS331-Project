from abc import ABC, abstractmethod
import hashlib

class User(ABC):
    def __init__(self, user_id: int, username: str, password: str):
        self._user_id = user_id
        self._username = username
        self._password_hash = self._hash_password(password)
        self._role = None

    def login(self, username: str, password: str) -> bool:
        return (
            self._username == username and
            self._password_hash == self._hash_password(password)
        )

    def logout(self) -> None:
        print(f"{self._username} logged out")

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def hasPermission(self, action: str) -> bool:
        return False

    @abstractmethod
    def get_role(self) -> str:
        pass
