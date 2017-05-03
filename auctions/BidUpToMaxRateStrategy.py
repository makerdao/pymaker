from auctions.StrategyResult import StrategyResult
from auctions.Strategy import Strategy
from contracts.Wad import Wad


class BidUpToMaxRateStrategy(Strategy):
    def __init__(self, max_price, step):
        self.max_price = max_price
        self.step = step
        assert(self.max_price > 0)
        assert(self.step > 0)
        assert(self.step <= 1)

    def perform(self, auctionlet, context):
        auction = auctionlet.get_auction()

        # get the current buy amount and the minimum possible increase
        auction_current_bid = auctionlet.buy_amount
        auction_min_next_bid = auction_current_bid.percentage_change(auction.min_increase)
        assert (auction_min_next_bid >= auction_current_bid)

        # calculate our maximum bid
        our_max_bid = auctionlet.sell_amount * self.max_price

        # if the current auction bid amount has already reached our maximum bid
        # then we can not go higher, so we do not bid
        if auction_current_bid >= our_max_bid:
            return StrategyResult("Our maximum possible bid reached")

        # if the auction next minimum bid is greater than our maximum bid
        # then we can not go higher, so we do not bid
        if auction_min_next_bid > our_max_bid:
            return StrategyResult("Minimal next bid exceeds our maximum possible bid")

        # this his how much we want to bid in ideal conditions...
        our_preferred_bid = auction_current_bid + (our_max_bid-auction_current_bid)*self.step
        # ...but we can still end up bidding more (because of the 'min_increase' auction parameter)
        our_preferred_bid = Wad.max(our_preferred_bid, auction_min_next_bid)

        # at the end, we cannot bid more than we actually have in our account
        our_balance = auction.buying.balance_of(context.trader_address)
        our_bid = Wad.min(our_preferred_bid, our_balance)

        if our_bid < auction_min_next_bid:
            if auctionlet.can_split():
                our_preferred_rate = our_preferred_bid/auctionlet.sell_amount
                our_bid = our_balance
                quantity = our_balance/our_preferred_rate

                bid_result = auctionlet.bid(our_bid, quantity)
                if bid_result:
                    return StrategyResult(f"Placed a new bid at {our_bid} {auction.buying.name()} (partial bid for {quantity} {auction.selling.name()}), bid was successful")
                else:
                    return StrategyResult(f"Tried to place a new bid at {our_bid} {auction.buying.name()} (partial bid for {quantity} {auction.selling.name()}), but the bid failed")
            else:
                return StrategyResult("Our available balance is below minimal next bid and splitting is unavailable")
        else:
            # we check our allowance, and raise it if necessary
            our_allowance = auction.buying.allowance_of(context.trader_address, context.auction_manager_address)
            if our_bid > our_allowance:
                if not auction.buying.approve(context.auction_manager_address, Wad(1000000*1000000000000000000)):
                    return StrategyResult(f"Tried to raise allowance, but the attempt failed")

            # a set of assertions to double-check our calculations
            assert (our_bid > auction_current_bid)
            assert (our_bid >= auction_min_next_bid)
            assert (our_bid <= our_max_bid)

            # TODO in order to test splitting auctions
            # if auctionlet._auction_manager.is_splitting:
            #     bid_result = auctionlet.bid(our_bid, auction.sell_amount-Wad(1000000000000000000))
            # else:
            bid_result = auctionlet.bid(our_bid)
            if bid_result:
                return StrategyResult(f"Placed a new bid at {our_bid} {auction.buying.name()}, bid was successful")
            else:
                return StrategyResult(f"Tried to place a new bid at {our_bid} {auction.buying.name()}, but the bid failed")
