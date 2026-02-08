from user_security.user import User

class Supervisor(User):
    def __init__(self, user_id, username, password):
        super().__init__(user_id, username, password)
        self._role = "SUPERVISOR"

    def approveAutomation(self) -> None:
        print("Automation approved")

    def monitorOperations(self) -> None:
        print("Monitoring operations")

    def get_role(self) -> str:
        return self._role
