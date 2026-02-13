class AutomationRule:
    def __init__(self, rule_id: int, condition: str, action: str):
        self._rule_id = rule_id
        self._condition = condition
        self._action = action

    def evaluate(self) -> bool:
        return True
