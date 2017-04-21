class ActionBid:
    def __init__(self, bid_amount):
        self.bid_amount = int(bid_amount)

    def __repr__(self):
        return f"ActionBid({self.bid_amount})"
