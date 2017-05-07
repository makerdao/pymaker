import math
import unittest

from unittest.mock import MagicMock

from auctions.BidUpToMaxRateStrategy import BidUpToMaxRateStrategy
from auctions.StrategyContext import StrategyContext
from contracts.Address import Address
from contracts.Wad import Wad
from contracts.auctions.AuctionManager import Auctionlet, Auction


class TestBidUpToMaxRateStrategy(unittest.TestCase):

    def setUp(self):
        self.auction_manager = MagicMock()
        self.auction_manager_address = Address('0x0101010101010101010101010101010101010101')
        self.dai_token = MagicMock()
        self.dai_token.name = MagicMock(return_value='DAI')
        self.dai_token_address = Address('0x0202020202020202020202020202020202020202')
        self.mkr_token = MagicMock()
        self.mkr_token.name = MagicMock(return_value='MKR')
        self.mkr_token_address = Address('0x0303030303030303030303030303030303030303')
        self.creator_address = Address('0x0404040404040404040404040404040404040404')
        self.our_address = Address('0x0505050505050505050505050505050505050505')
        self.competitor_address = Address('0x0606060606060606060606060606060606060606')
        self.auction = Auction(self.auction_manager, 1, [self.creator_address, self.dai_token_address, self.mkr_token_address, 0, 1, 0, 0, 120, False, False])
        self.auction.selling = self.dai_token
        self.auction.buying = self.mkr_token
        self.auctionlet = Auctionlet(self.auction_manager, 1, [1, Address('0x0000000000000000000000000000000000000000'), 1493817473, 0, 0, True, 1], False)
        self.auctionlet.get_auction = MagicMock(return_value=self.auction)
        self.auctionlet.bid = MagicMock(return_value=True)
        self.context = StrategyContext(self.auction_manager_address, self.our_address)
        self.lots_of_money = Wad(1000000000*1000000000000000000)
        self.auction.sell_amount = Wad(10*self.wei())
        self.auction.start_bid = Wad(1*self.wei())
        self.auctionlet.buy_amount = self.auction.start_bid
        self.auctionlet.sell_amount = self.auction.sell_amount
        self.auctionlet.last_bidder = self.creator_address
        self.set_mkr_balance(self.lots_of_money)
        self.set_mkr_allowance(self.lots_of_money)

    def set_mkr_balance(self, value):
        self.mkr_token.balance_of = MagicMock(self.our_address, return_value=value)

    def set_mkr_allowance(self, value):
        self.mkr_token.allowance_of = MagicMock([self.our_address, self.auction_manager_address], return_value=value)

    def wei(self):
        return int(math.pow(10, 18))

    def test_should_bid_on_newly_created_auctions(self):
        # given
        # (newly created auction)

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at 100.500000000000000000 MKR, bid was successful. Our maximum bid on this auctionlet is 200.000000000000000000 MKR", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(100.5*self.wei()))

    def test_should_overbid_competitors(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at 125.000000000000000000 MKR, bid was successful. Our maximum bid on this auctionlet is 200.000000000000000000 MKR", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(125*self.wei()))

    def test_should_not_bid_over_max_price(self):
        # given
        self.auctionlet.buy_amount = Wad(200*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Our maximum possible bid (200.000000000000000000 MKR) reached", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_not_called()

    def test_should_not_bid_if_min_increase_would_go_over_max_price(self):
        # given
        self.auction.min_increase = 3
        self.auctionlet.buy_amount = Wad(195*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Minimal increase (200.850000000000000000 MKR) exceeds our maximum possible bid (200.000000000000000000 MKR)", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_not_called()

    def test_should_not_bid_if_minimal_bid_is_over_max_price(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(201 * self.wei()))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Minimal allowed bid (201.000000000000000000 MKR) exceeds our maximum possible bid (200.000000000000000000 MKR)", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_not_called()

    def test_should_place_bids_not_lower_thanminimal_bid(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(190 * self.wei()))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at 190.000000000000000000 MKR, bid was successful. Our maximum bid on this auctionlet is 200.000000000000000000 MKR", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(190*self.wei()))

    def test_should_still_bid_if_minimal_bid_is_equal_to_max_price(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(200 * self.wei()))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at 200.000000000000000000 MKR, bid was successful", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(200*self.wei()))

    def test_should_bid_more_than_step_because_of_min_increase(self):
        # given
        self.auction.min_increase = 2
        self.auctionlet.buy_amount = Wad(195*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at 198.900000000000000000 MKR, bid was successful. Our maximum bid on this auctionlet is 200.000000000000000000 MKR", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(198.9*self.wei()))

    def test_should_bid_normally_if_min_increase_is_low(self):
        # given
        self.auction.min_increase = 1
        self.auctionlet.buy_amount = Wad(195*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at 197.500000000000000000 MKR, bid was successful. Our maximum bid on this auctionlet is 200.000000000000000000 MKR", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(197.5*self.wei()))

    def test_should_limit_bids_by_available_balance(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address
        self.set_mkr_balance(Wad(79 * self.wei()))

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at 79.000000000000000000 MKR, bid was successful. Our maximum bid on this auctionlet is 200.000000000000000000 MKR", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(79*self.wei()))

    def test_should_not_bid_if_available_balance_below_minimal_bid(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address
        self.auctionlet.can_split = MagicMock(return_value=False)
        self.set_mkr_balance(Wad(60 * self.wei()))

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(65 * self.wei()))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Not bidding as available balance (60.000000000000000000 MKR) is less than minimal allowed bid (65.000000000000000000 MKR)", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_not_called()

    def test_should_still_bid_if_available_balance_equal_to_minimal_bid(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address
        self.auctionlet.can_split = MagicMock(return_value=False)
        self.set_mkr_balance(Wad(60 * self.wei()))

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(60 * self.wei()))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at 60.000000000000000000 MKR, bid was successful. Our maximum bid on this auctionlet is 200.000000000000000000 MKR", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(60*self.wei()))

    def test_should_make_a_partial_bid_if_available_balance_below_min_increase_and_can_split(self):
        # given
        self.auction.min_increase = 10
        self.auction.can_split = MagicMock(return_value=False)
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address
        self.auctionlet.can_split = MagicMock(return_value=True)
        self.set_mkr_balance(Wad(54 * self.wei()))

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new partial bid at 54.000000000000000000 MKR (for 4.320000000000000000 DAI), bid was successful, new auctionlet got created", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(54*self.wei()), Wad(4320000000000000000))

    def test_should_not_make_a_partial_bid_if_available_balance_below_min_increase_and_cannot_split(self):
        # given
        self.auction.min_increase = 15
        self.auction.can_split = MagicMock(return_value=False)
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address
        self.auctionlet.can_split = MagicMock(return_value=False)
        self.set_mkr_balance(Wad(54 * self.wei()))

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Our available balance (54.000000000000000000 MKR is below minimal next bid (57.500000000000000000 MKR) and splitting is unavailable", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_not_called()

    def test_should_not_make_a_partial_bid_if_available_balance_below_minimum_bid(self):
        # given
        self.auction.min_increase = 15
        self.auction.can_split = MagicMock(return_value=False)
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address
        self.auctionlet.can_split = MagicMock(return_value=True)
        self.set_mkr_balance(Wad(54 * self.wei()))

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(55 * self.wei()))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Not bidding as available balance (54.000000000000000000 MKR) is less than minimal allowed bid (55.000000000000000000 MKR)", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_not_called()

    def test_should_make_a_partial_bid_ensuring_relative_increase_in_value(self):
        # given
        self.auction.min_increase = 20
        self.auction.can_split = MagicMock(return_value=False)
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address
        self.auctionlet.can_split = MagicMock(return_value=True)
        self.set_mkr_balance(Wad(54 * self.wei()))

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.05, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new partial bid at 54.000000000000000000 MKR (for 9.000000000000000000 DAI), bid was successful, new auctionlet got created", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(54*self.wei()), Wad(9*self.wei()))

    def test_should_raise_allowance_if_too_low_before_bidding(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address
        self.set_mkr_allowance(Wad(52 * self.wei()))
        self.mkr_token.approve = MagicMock(return_value=True)

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at 125.000000000000000000 MKR, bid was successful. Our maximum bid on this auctionlet is 200.000000000000000000 MKR", result.description)
        self.assertFalse(result.forget)
        self.mkr_token.approve.assert_called_once_with(self.auction_manager_address, Wad(1000000*self.wei()))
        self.auctionlet.bid.assert_called_once_with(Wad(125*self.wei()))

    def test_should_fail_if_unable_to_raise_allowance(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address
        self.set_mkr_allowance(Wad(52 * self.wei()))
        self.mkr_token.approve = MagicMock(return_value=False)

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Tried to raise MKR allowance, but the attempt failed", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_not_called()

    def test_should_fail_if_unable_to_bid(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address
        self.auctionlet.bid = MagicMock(return_value=False)

        # when
        strategy = BidUpToMaxRateStrategy(0.05, 0.5, Wad(1))
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Tried to place a new bid at 125.000000000000000000 MKR, but the bid failed", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(125*self.wei()))


if __name__ == '__main__':
    unittest.main()
