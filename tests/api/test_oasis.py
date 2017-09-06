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

from unittest.mock import Mock

import pytest
from web3 import EthereumTesterProvider
from web3 import Web3

from keeper.api import Address, Wad
from keeper.api.approval import directly
from keeper.api.oasis import SimpleMarket, ExpiringMarket, MatchingMarket
from keeper.api.token import DSToken
from tests.api.helpers import wait_until_mock_called

PAST_BLOCKS = 100


class GeneralMarketTest:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.token1 = DSToken.deploy(self.web3, 'AAA')
        self.token1.mint(Wad.from_number(100)).transact()
        self.token2 = DSToken.deploy(self.web3, 'BBB')
        self.token2.mint(Wad.from_number(100)).transact()
        self.otc = None

    def test_approve_and_make_and_getters(self):
        # given
        assert self.otc.get_last_offer_id() == 0

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # then
        assert self.otc.get_last_offer_id() == 1

        # and
        assert self.otc.get_offer(1).offer_id == 1
        assert self.otc.get_offer(1).sell_which_token == self.token1.address
        assert self.otc.get_offer(1).sell_how_much == Wad.from_number(1)
        assert self.otc.get_offer(1).buy_which_token == self.token2.address
        assert self.otc.get_offer(1).buy_how_much == Wad.from_number(2)
        assert self.otc.get_offer(1).owner == self.our_address
        assert self.otc.get_offer(1).timestamp != 0

        # and
        assert self.otc.active_offers() == [self.otc.get_offer(1)]

    def test_offer_comparison(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # and
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(3),
                      want_token=self.token2.address, want_amount=Wad.from_number(4)).transact()

        # then
        assert self.otc.get_last_offer_id() == 2
        assert self.otc.get_offer(1) == self.otc.get_offer(1)
        assert self.otc.get_offer(1) != self.otc.get_offer(2)

    def test_take_partial(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # when
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.25)).transact()

        # then
        assert self.otc.get_offer(1).sell_how_much == Wad.from_number(0.75)
        assert self.otc.get_offer(1).buy_how_much == Wad.from_number(1.5)
        assert self.otc.active_offers() == [self.otc.get_offer(1)]
        assert self.otc.get_last_offer_id() == 1

    def test_take_complete(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # when
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(1)).transact()

        # then
        assert self.otc.get_offer(1) is None
        assert self.otc.active_offers() == []
        assert self.otc.get_last_offer_id() == 1

    def test_kill(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # when
        self.otc.kill(1).transact({'gas': 4000000})

        # then
        assert self.otc.get_offer(1) is None
        assert self.otc.active_offers() == []
        assert self.otc.get_last_offer_id() == 1

    def test_no_past_events_on_startup(self):
        assert self.otc.past_make(PAST_BLOCKS) == []
        assert self.otc.past_bump(PAST_BLOCKS) == []
        assert self.otc.past_take(PAST_BLOCKS) == []
        assert self.otc.past_kill(PAST_BLOCKS) == []

    def test_past_make(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # then
        past_make = self.otc.past_make(PAST_BLOCKS)
        assert len(past_make) == 1
        assert past_make[0].id == 1
        assert past_make[0].maker == self.our_address
        assert past_make[0].pay_token == self.token1.address
        assert past_make[0].pay_amount == Wad.from_number(1)
        assert past_make[0].buy_token == self.token2.address
        assert past_make[0].buy_amount == Wad.from_number(2)
        assert past_make[0].timestamp != 0

    def test_past_take(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # and
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.5)).transact()

        # then
        past_take = self.otc.past_take(PAST_BLOCKS)
        assert len(past_take) == 1
        assert past_take[0].id == 1
        assert past_take[0].maker == self.our_address
        assert past_take[0].taker == self.our_address
        assert past_take[0].pay_token == self.token1.address
        assert past_take[0].buy_token == self.token2.address
        assert past_take[0].take_amount == Wad.from_number(0.5)
        assert past_take[0].give_amount == Wad.from_number(1)
        assert past_take[0].timestamp != 0

    def test_past_kill(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # and
        self.otc.kill(1).transact()

        # then
        past_kill = self.otc.past_kill(PAST_BLOCKS)
        assert len(past_kill) == 1
        assert past_kill[0].id == 1
        assert past_kill[0].maker == self.our_address
        assert past_kill[0].pay_token == self.token1.address
        assert past_kill[0].pay_amount == Wad.from_number(1)
        assert past_kill[0].buy_token == self.token2.address
        assert past_kill[0].buy_amount == Wad.from_number(2)
        assert past_kill[0].timestamp != 0

    @pytest.mark.timeout(5)
    def test_on_make(self):
        # given
        on_make_mock = Mock()
        self.otc.on_make(on_make_mock)

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # then
        on_make = wait_until_mock_called(on_make_mock)[0]
        assert on_make.id == 1
        assert on_make.maker == self.our_address
        assert on_make.pay_token == self.token1.address
        assert on_make.pay_amount == Wad.from_number(1)
        assert on_make.buy_token == self.token2.address
        assert on_make.buy_amount == Wad.from_number(2)
        assert on_make.timestamp != 0

    @pytest.mark.timeout(5)
    def test_on_take(self):
        # given
        on_take_mock = Mock()
        self.otc.on_take(on_take_mock)

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # and
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.5)).transact()

        # then
        on_take = wait_until_mock_called(on_take_mock)[0]
        assert on_take.id == 1
        assert on_take.maker == self.our_address
        assert on_take.taker == self.our_address
        assert on_take.pay_token == self.token1.address
        assert on_take.buy_token == self.token2.address
        assert on_take.take_amount == Wad.from_number(0.5)
        assert on_take.give_amount == Wad.from_number(1)
        assert on_take.timestamp != 0

    @pytest.mark.timeout(5)
    def test_on_kill(self):
        # given
        on_kill_mock = Mock()
        self.otc.on_kill(on_kill_mock)

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # and
        self.otc.kill(1).transact()

        # then
        on_kill = wait_until_mock_called(on_kill_mock)[0]
        assert on_kill.id == 1
        assert on_kill.maker == self.our_address
        assert on_kill.pay_token == self.token1.address
        assert on_kill.pay_amount == Wad.from_number(1)
        assert on_kill.buy_token == self.token2.address
        assert on_kill.buy_amount == Wad.from_number(2)
        assert on_kill.timestamp != 0


class TestSimpleMarket(GeneralMarketTest):
    def setup_method(self):
        GeneralMarketTest.setup_method(self)
        self.otc = SimpleMarket.deploy(self.web3)

    def test_should_have_printable_representation(self):
        assert repr(self.otc) == f"SimpleMarket('{self.otc.address}')"


class TestExpiringMarket(GeneralMarketTest):
    def setup_method(self):
        GeneralMarketTest.setup_method(self)
        self.otc = ExpiringMarket.deploy(self.web3, 2500000000)

    def test_should_have_printable_representation(self):
        assert repr(self.otc) == f"ExpiringMarket('{self.otc.address}')"


class TestMatchingMarket(GeneralMarketTest):
    def setup_method(self):
        GeneralMarketTest.setup_method(self)
        self.otc = MatchingMarket.deploy(self.web3, 2500000000)
        self.otc.add_token_pair_whitelist(self.token1.address, self.token2.address).transact()
        self.otc.set_matching_enabled(False).transact()

    def test_should_have_printable_representation(self):
        assert repr(self.otc) == f"MatchingMarket('{self.otc.address}')"
