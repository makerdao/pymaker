from auctions.StrategyResult import StrategyResult
from auctions.Strategy import Strategy


class HandleExpiredAuctionletsStrategy(Strategy):
    def __init__(self, next_strategy):
        self.next_strategy = next_strategy

    def perform(self, auctionlet, context):
        if auctionlet.expired:
            if auctionlet.unclaimed and (auctionlet.last_bidder == context.trader_address):
                claim_result = auctionlet.claim()
                if claim_result:
                    return StrategyResult("Expired, we won, claimed by us successfully. Forgetting it.", forget=True)
                else:
                    return StrategyResult("Expired, we won, tried to claim it but claim failed")
            else:
                return StrategyResult('Expired, waiting to be claimed by somebody else. Forgetting it.', forget=True)
        else:
            return self.next_strategy.perform(auctionlet, context)
