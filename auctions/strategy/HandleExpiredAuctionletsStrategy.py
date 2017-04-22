from auctions.Result import Result
from auctions.strategy.Strategy import Strategy


class HandleExpiredAuctionletsStrategy(Strategy):
    def __init__(self, next_strategy):
        self.next_strategy = next_strategy

    def perform(self, auctionlet, context):
        if auctionlet.is_expired():
            auctionlet_info = auctionlet.get_info()
            if auctionlet_info.unclaimed and (auctionlet_info.last_bidder == context.trader_address):
                claim_result = auctionlet.claim()
                if claim_result:
                    return Result(f"Expired, we won, claimed by us successfully.", forget=True)
                else:
                    return Result(f"Expired, we won, tried to claim it but it failed")
            else:
                return Result('Expired, waiting to be claimed by somebody else. Removing.', forget=True)
        else:
            return self.next_strategy.perform(auctionlet, context)
