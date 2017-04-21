class ActionPass:
    def __init__(self, reason):
        self.reason = reason

    def __repr__(self):
        return f"ActionPass('{self.reason}')"
