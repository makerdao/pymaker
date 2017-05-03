import unittest

import datetime
from unittest.mock import MagicMock

import math

from auctions.BidUpToMaxRateStrategy import BidUpToMaxRateStrategy
from auctions.StrategyContext import StrategyContext
from contracts.Address import Address
from contracts.Wad import Wad
from contracts.auctions.AuctionManager import Auctionlet, Auction


class TestBidUpToMaxRateStrategy(unittest.TestCase):

    def setUp(self):
        self.auction_manager = MagicMock()
        self.auction_manager_address = Address('0xcd2a3d9f938e13cd947ec05abc7fe734df8dd826')
        self.dai_token = MagicMock
        self.dai_token.name = MagicMock(return_value='DAI')
        self.dai_token_address = Address('0x0404010101010101010101010101010101010101')
        self.mkr_token = MagicMock
        self.mkr_token.name = MagicMock(return_value='MKR')
        self.mkr_token_address = Address('0x0505050101010101010101010101010101010101')
        self.creator_address = Address('0x0303010101010101010101010101010101010101')
        self.our_address = Address('0x0101010101010101010101010101010101010101')
        self.competitor_address = Address('0x0202010101010101010101010101010101010101')
        self.auction = Auction(self.auction_manager, 1, [self.creator_address, self.dai_token_address, self.mkr_token_address, self.int_value(1), 1, 0, self.int_value(1), 120, False, False])
        self.auction.selling = self.dai_token
        self.auction.buying = self.mkr_token
        self.auctionlet = Auctionlet(self.auction_manager, 1, [1, Address('0x0000000000000000000000000000000000000000'), 1493817473, self.int_value(1), self.int_value(1), True, 1])
        self.auctionlet.get_auction = MagicMock(return_value=self.auction)
        self.auctionlet.bid = MagicMock(return_value=True)
        self.context = StrategyContext(self.auction_manager_address, self.our_address)
        self.lots_of_money = Wad(1000000000*1000000000000000000)
        self.auction.sell_amount = Wad(10*self.wei())
        self.auction.start_bid = Wad(1*self.wei())
        self.auctionlet.buy_amount = self.auction.start_bid
        self.auctionlet.sell_amount = self.auction.sell_amount
        self.auctionlet.last_bidder = self.creator_address
        self.mkr_balance(self.lots_of_money)
        self.mkr_allowance(self.lots_of_money)

    def test_should_bid_on_newly_created_auctions(self):
        # when
        strategy = BidUpToMaxRateStrategy(20, 0.5)
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at    100.500000000000000000 MKR, bid was successful", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(100.5*self.wei()))

    def test_should_overbid_competitors(self):
        # given
        self.auctionlet.buy_amount = Wad(50*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(20, 0.5)
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at    125.000000000000000000 MKR, bid was successful", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(125*self.wei()))

    def test_should_not_bid_over_max_price(self):
        # given
        self.auctionlet.buy_amount = Wad(200*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(20, 0.5)
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Our maximum possible bid reached", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_not_called()

    def test_should_not_bid_under_min_increase(self):
        # given
        self.auction.min_increase = 3
        self.auctionlet.buy_amount = Wad(195*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(20, 0.5)
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Minimal next bid exceeds our maximum possible bid", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_not_called()

    def test_should_bid_over_min_increase(self):
        # given
        self.auction.min_increase = 1
        self.auctionlet.buy_amount = Wad(195*self.wei())
        self.auctionlet.last_bidder = self.competitor_address

        # when
        strategy = BidUpToMaxRateStrategy(20, 0.5)
        result = strategy.perform(self.auctionlet, self.context)

        # then
        self.assertEqual("Placed a new bid at    197.500000000000000000 MKR, bid was successful", result.description)
        self.assertFalse(result.forget)
        self.auctionlet.bid.assert_called_once_with(Wad(197.5*self.wei()))


    def mkr_balance(self, value):
        self.mkr_token.balance_of = MagicMock(self.our_address, return_value=value)

    def mkr_allowance(self, value):
        self.mkr_token.allowance_of = MagicMock([self.our_address, self.auction_manager_address], return_value=value)

    def wei(self):
        return math.pow(10, 18)

    def int_value(self, value):
        return value*math.pow(10, 18)

    def wad_value(self, value):
        return Wad(self.int_value(value))


if __name__ == '__main__':
    unittest.main()
