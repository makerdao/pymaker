from auctions.ActionBid import ActionBid
from auctions.ActionPass import ActionPass
from contracts.Address import Address
import math


class DumbStrategy:
    def __init__(self, token_sell, token_buy, max_sell_to_buy_rate, percentage_step):
        self.token_sell = token_sell
        self.token_buy = token_buy
        self.max_sell_to_buy_rate = max_sell_to_buy_rate
        self.percentage_step = percentage_step

    def action(self, auction_info, auctionlet_info, auctioning_address, auction_manager_address):
        # we trade only on our token pair
        if auction_info.selling != Address(self.token_sell.address): return ActionPass("Not our token pair")
        if auction_info.buying != Address(self.token_buy.address): return ActionPass("Not our token pair")

        # we trade only if we are not already winning the auction
        # TODO

        # get the current buy amount and the minimum possible increase
        auction_current_bid = auctionlet_info.buy_amount
        auction_min_next_bid = int(math.ceil(auction_current_bid * (100 + auction_info.min_increase) / 100))
        assert (auction_min_next_bid >= auction_current_bid)

        # calculate our maximum bid
        our_max_bid = auctionlet_info.sell_amount * self.max_sell_to_buy_rate

        # if the current auction bid amount has already reached our maximum bid
        # then we can not go higher, so we do not bid
        if auction_current_bid >= our_max_bid:
            return ActionPass("Our maximum possible bid reached")

        # if the auction next minimum bid is greater than our maximum bid
        # then we can not go higher, so we do not bid
        if auction_min_next_bid > our_max_bid:
            return ActionPass("Minimal next bid exceeds our maximum possible bid")

        # this his how much we want to bid in ideal conditions...
        our_preferred_bid = int(auction_current_bid + (our_max_bid-auction_current_bid)*self.percentage_step)
        # ...but we can still end up bidding more (because of the 'min_increase' auction parameter)
        our_preferred_bid = int(max(our_preferred_bid, auction_min_next_bid))

        # at the end, we cannot bid more than we actually have in our account
        our_balance = self.token_buy.balance_of(auctioning_address)
        our_bid = int(min(our_preferred_bid, our_balance))

        # we check our allowance, as we cannot bid above it
        our_allowance = self.token_buy.allowance_of(auctioning_address, auction_manager_address)


        if (our_bid <= auction_current_bid):
            return ActionPass("Our available balance is less or equal to the current auction bid")
        elif (our_bid < auction_min_next_bid):
            return ActionPass("Our available balance is below minimal next bid")
        elif (our_bid > our_allowance):
            return ActionPass("Allowance is too low, please raise allowance in order to continue auctioning")
        else:
            # a set of assertions to double-check our calculations
            assert (our_bid > auction_current_bid)
            assert (our_bid > auction_min_next_bid)
            assert (our_bid <= our_max_bid)
            return ActionBid(our_bid)
