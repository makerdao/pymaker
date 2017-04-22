from auctions.StrategyResult import StrategyResult
from auctions.Strategy import Strategy


# we trade only on our token pair
class IgnoreWinningAuctionletsStrategy(Strategy):
    def __init__(self, next_strategy):
        self.next_strategy = next_strategy

    def perform(self, auctionlet, context):
        auctionlet_info = auctionlet.get_info()
        if auctionlet_info.last_bidder == context.trader_address:
            return StrategyResult('We are the highest bidder. Not doing anything.')
        else:
            return self.next_strategy.perform(auctionlet, context)
