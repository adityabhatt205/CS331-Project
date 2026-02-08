from user_security.user import User

class Operator(User):
    def __init__(self, user_id, username, password):
        super().__init__(user_id, username, password)
        self._role = "OPERATOR"

    def controlMachines(self) -> None:
        print("Controlling machines")

    def viewLiveStatus(self) -> None:
        print("Viewing live status")

    def get_role(self) -> str:
        return self._role
