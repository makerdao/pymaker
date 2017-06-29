# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from api.token import ERC20Token
from api.numeric import Wad
from keepers.auctions.Strategy import Strategy
from keepers.auctions.StrategyResult import StrategyResult


class BasicForwardAuctionStrategy(Strategy):
    def __init__(self, we_buy, we_sell, mkr_dai_rate, step, minimal_bid):
        self.we_buy = we_buy
        self.we_sell = we_sell
        self.mkr_dai_rate = mkr_dai_rate
        self.step = step
        self.minimal_bid = minimal_bid
        assert(isinstance(self.we_buy, ERC20Token))
        assert(isinstance(self.we_sell, ERC20Token))
        assert(self.mkr_dai_rate > 0)
        assert(self.step > 0)
        assert(self.step <= 1)
        assert(isinstance(self.minimal_bid, Wad))
        assert(self.minimal_bid > Wad(0))

    def perform(self, auctionlet, context):
        auction = auctionlet.get_auction()

        # this strategy supports forward auctions only
        if not auction.is_forward():
            return StrategyResult(f"Not a forward auction. Forgetting it.", forget=True)

        # we trade only on our token pair
        if (auction.selling != self.we_buy) or (auction.buying != self.we_sell):
            return StrategyResult("Unrecognized token pair. Forgetting it.", forget=True)

        # we do not do anything if we are already winning
        if auctionlet.last_bidder == context.trader_address:
            return StrategyResult('We are the highest bidder. Not doing anything.')

        # handle expired auctions, we either claim them or forget them
        if auctionlet.expired:
            if auctionlet.unclaimed:
                if auctionlet.last_bidder == context.trader_address:
                    if auctionlet.claim():
                        return StrategyResult("Expired and unclaimed, we won, claimed by us successfully. Forgetting it.", forget=True)
                    else:
                        return StrategyResult("Expired and unclaimed, we won, tried to claim it but claim failed")
                else:
                    return StrategyResult('Expired and unclaimed, waiting to be claimed by somebody else. Forgetting it.', forget=True)
            else:
                return StrategyResult('Expired and claimed. Forgetting it.', forget=True)

        # get the current buy amount and the minimum possible increase
        auction_current_bid = auctionlet.buy_amount
        auction_min_next_bid = auction_current_bid.percentage_change(auction.min_increase)
        assert (auction_min_next_bid >= auction_current_bid)

        # calculate our maximum bid
        our_max_bid = auctionlet.sell_amount / self.mkr_dai_rate

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
                    return StrategyResult(f"Placed a new partial bid at {our_bid} {auction.buying.name()} (for {quantity} {auction.selling.name()}), bid was successful, new auctionlet got created")
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
                    return StrategyResult(f"Placed a new bid at {our_bid} {auction.buying.name()}, bid was successful. Our maximum bid on this auctionlet is {our_max_bid} {auction.buying.name()}")
                else:
                    return StrategyResult(f"Placed a new bid at {our_bid} {auction.buying.name()}, bid was successful")
            else:
                return StrategyResult(f"Tried to place a new bid at {our_bid} {auction.buying.name()}, but the bid failed")

    @staticmethod
    def _ensure_allowance(auction, context, bid_amount):
        our_allowance = auction.buying.allowance_of(context.trader_address, context.auction_manager_address)
        if bid_amount > our_allowance:
            return auction.buying.approve(context.auction_manager_address)
        else:
            return True
