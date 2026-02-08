from user_security.user import User

class Admin(User):
    def __init__(self, user_id, username, password):
        super().__init__(user_id, username, password)
        self._role = "ADMIN"

    def manageUsers(self) -> None:
        print("Managing users")

    def configureAutomationRules(self) -> None:
        print("Configuring automation rules")

    def get_role(self) -> str:
        return self._role
