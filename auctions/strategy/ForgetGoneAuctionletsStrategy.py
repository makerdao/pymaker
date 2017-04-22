from auctions.Result import Result
from auctions.strategy.Strategy import Strategy


class ForgetGoneAuctionletsStrategy(Strategy):
    def __init__(self, next_strategy):
        self.next_strategy = next_strategy

    def perform(self, auctionlet, context):
        auctionlet_info = auctionlet.get_info()
        auctionlet_expired = auctionlet.is_expired()

        # for expired&claimed auctionlets, these methods return None
        if (auctionlet_info is None) or (auctionlet_expired is None):
            return Result('Auctionlet is already gone. Removing.', forget=True)
        else:
            return self.next_strategy.perform(auctionlet, context)
