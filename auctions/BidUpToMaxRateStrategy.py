import math

from auctions.StrategyResult import StrategyResult
from auctions.Strategy import Strategy


class BidUpToMaxRateStrategy(Strategy):
    def __init__(self, max_rate_offered, percentage_step):
        self.max_rate_offered = max_rate_offered
        self.percentage_step = percentage_step

    def perform(self, auctionlet, context):
        auction_info = auctionlet.get_auction().get_info()

        # get the current buy amount and the minimum possible increase
        auction_current_bid = auctionlet.buy_amount
        auction_min_next_bid = int(math.ceil(auction_current_bid * (100 + auction_info.min_increase) / 100))
        assert (auction_min_next_bid >= auction_current_bid)

        # calculate our maximum bid
        our_max_bid = auctionlet.sell_amount * self.max_rate_offered

        # if the current auction bid amount has already reached our maximum bid
        # then we can not go higher, so we do not bid
        if auction_current_bid >= our_max_bid:
            return StrategyResult("Our maximum possible bid reached")

        # if the auction next minimum bid is greater than our maximum bid
        # then we can not go higher, so we do not bid
        if auction_min_next_bid > our_max_bid:
            return StrategyResult("Minimal next bid exceeds our maximum possible bid")

        # this his how much we want to bid in ideal conditions...
        our_preferred_bid = int(auction_current_bid + (our_max_bid-auction_current_bid)*self.percentage_step)
        # ...but we can still end up bidding more (because of the 'min_increase' auction parameter)
        our_preferred_bid = int(max(our_preferred_bid, auction_min_next_bid))

        # at the end, we cannot bid more than we actually have in our account
        our_balance = auction_info.buying.balance_of(context.trader_address)
        our_bid = int(min(our_preferred_bid, our_balance))

        # we check our allowance, as we cannot bid above it
        our_allowance = auction_info.buying.allowance_of(context.trader_address, context.auction_manager_address)

        if our_bid <= auction_current_bid:
            return StrategyResult("Our available balance is less or equal to the current auction bid")
        elif our_bid < auction_min_next_bid:
            return StrategyResult("Our available balance is below minimal next bid")
        elif our_bid > our_allowance:
            return StrategyResult("Allowance is too low, please raise allowance in order to continue participating")
        else:
            # a set of assertions to double-check our calculations
            assert (our_bid > auction_current_bid)
            assert (our_bid > auction_min_next_bid)
            assert (our_bid <= our_max_bid)

            bid_result = auctionlet.bid(our_bid)
            if bid_result:
                return StrategyResult(f"Placed a bid at {our_bid}, bid was successful")
            else:
                return StrategyResult(f"Tried to place a bid at {our_bid}, but the bid failed")
