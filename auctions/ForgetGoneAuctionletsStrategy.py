from auctions.StrategyResult import StrategyResult
from auctions.Strategy import Strategy


class ForgetGoneAuctionletsStrategy(Strategy):
    def __init__(self, next_strategy):
        self.next_strategy = next_strategy

    def perform(self, auctionlet, context):
        auctionlet_expired = auctionlet.is_expired() if auctionlet is not None else None

        # for expired&claimed auctionlets, these methods return None
        if (auctionlet is None) or (auctionlet_expired is None):
            return StrategyResult('Auctionlet is already gone. Forgetting it.', forget=True)
        else:
            return self.next_strategy.perform(auctionlet, context)
