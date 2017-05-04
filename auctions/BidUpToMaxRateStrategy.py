from auctions.StrategyResult import StrategyResult
from auctions.Strategy import Strategy
from contracts.Wad import Wad


class BidUpToMaxRateStrategy(Strategy):
    def __init__(self, max_price, step, minimal_bid):
        self.max_price = max_price
        self.step = step
        self.minimal_bid = minimal_bid
        assert(self.max_price > 0)
        assert(self.step > 0)
        assert(self.step <= 1)
        assert(isinstance(self.minimal_bid, Wad))
        assert(self.minimal_bid > Wad(0))

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
            return StrategyResult(f"Our maximum possible bid ({our_max_bid} {auction.buying.name()}) reached")

        # if the auction next minimum increase is greater than our maximum possible bid
        # then we can not go higher, so we do not bid
        if auction_min_next_bid > our_max_bid:
            return StrategyResult(f"Minimal increase ({auction_min_next_bid} {auction.buying.name()}) exceeds our maximum possible bid ({our_max_bid} {auction.buying.name()})")

        # if the our global minimal bid is greater than our maximum possible bid then we do not bid
        if self.minimal_bid > our_max_bid:
            return StrategyResult(f"Minimal allowed bid ({self.minimal_bid} {auction.buying.name()}) exceeds our maximum possible bid ({our_max_bid} {auction.buying.name()})")

        # we never bid if our available balance is below global minimal bid
        our_balance = auction.buying.balance_of(context.trader_address)
        if our_balance < self.minimal_bid:
            return StrategyResult(f"Not bidding as available balance ({our_balance} {auction.buying.name()}) is less than minimal allowed bid ({self.minimal_bid} {auction.buying.name()})")

        # this his how much we want to bid in ideal conditions...
        our_preferred_bid = auction_current_bid + (our_max_bid-auction_current_bid)*self.step
        # ...but we can still end up bidding more (either because of the 'min_increase' auction parameter...
        our_preferred_bid = Wad.max(our_preferred_bid, auction_min_next_bid)
        # ...or because of the global minimal bid)
        our_preferred_bid = Wad.max(our_preferred_bid, self.minimal_bid)

        # at the end, we cannot bid more than we actually have in our account
        our_bid = Wad.min(our_preferred_bid, our_balance)

        if our_bid < auction_min_next_bid:
            if auctionlet.can_split():
                our_preferred_rate = our_preferred_bid/auctionlet.sell_amount
                our_bid = our_balance
                quantity = our_balance/our_preferred_rate

                # we check our allowance, and raise it if necessary
                if not self._ensure_allowance(auction, context, our_bid):
                    return StrategyResult(f"Tried to raise {auction.buying.name()} allowance, but the attempt failed")

                if auctionlet.bid(our_bid, quantity):
                    return StrategyResult(f"Placed a new bid at {our_bid} {auction.buying.name()} (partial bid for {quantity} {auction.selling.name()}), bid was successful")
                else:
                    return StrategyResult(f"Tried to place a new bid at {our_bid} {auction.buying.name()} (partial bid for {quantity} {auction.selling.name()}), but the bid failed")
            else:
                return StrategyResult(f"Our available balance ({our_balance} {auction.buying.name()} is below minimal next bid ({auction_min_next_bid} {auction.buying.name()}) and splitting is unavailable")
        else:
            # we check our allowance, and raise it if necessary
            if not self._ensure_allowance(auction, context, our_bid):
                return StrategyResult(f"Tried to raise {auction.buying.name()} allowance, but the attempt failed")

            # a set of assertions to double-check our calculations
            assert (our_bid > auction_current_bid)
            assert (our_bid >= auction_min_next_bid)
            assert (our_bid <= our_max_bid)

            if auctionlet.bid(our_bid):
                if our_bid < our_max_bid:
                    return StrategyResult(f"Placed a new bid at {our_bid} {auction.buying.name()}, bid was successful. Will carry on bidding up to {our_max_bid} {auction.buying.name()}")
                else:
                    return StrategyResult(f"Placed a new bid at {our_bid} {auction.buying.name()}, bid was successful")
            else:
                return StrategyResult(f"Tried to place a new bid at {our_bid} {auction.buying.name()}, but the bid failed")

    @staticmethod
    def _ensure_allowance(auction, context, bid_amount):
        our_allowance = auction.buying.allowance_of(context.trader_address, context.auction_manager_address)
        if bid_amount > our_allowance:
            return auction.buying.approve(context.auction_manager_address, Wad(1000000*1000000000000000000))
        else:
            return True
