from auctions.StrategyResult import StrategyResult
from auctions.Strategy import Strategy


# we trade only on our token pair
class OnlyOurPairStrategy(Strategy):
    def __init__(self, token_sell, token_buy, next_strategy):
        self.token_sell = token_sell
        self.token_buy = token_buy
        self.next_strategy = next_strategy

    def perform(self, auctionlet, context):
        auction_info = auctionlet.get_auction().get_info()
        if (auction_info.selling == self.token_sell) and (auction_info.buying == self.token_buy):
            return self.next_strategy.perform(auctionlet, context)
        else:
            return StrategyResult("Not our token pair. Forgetting it.", forget=True)
