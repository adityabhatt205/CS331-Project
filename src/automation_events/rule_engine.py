class RuleEngine:
    def __init__(self):
        self._rules = []

    def executeRules(self) -> None:
        for rule in self._rules:
            if rule.evaluate():
                print("Rule triggered")

    def validateRule(self, rule) -> bool:
        return True
