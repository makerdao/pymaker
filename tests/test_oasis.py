# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
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
from typing import List
from unittest.mock import Mock

import pytest
import time
from web3 import EthereumTesterProvider
from web3 import Web3

from pymaker import Address, Wad
from pymaker.approval import directly
from pymaker.oasis import SimpleMarket, ExpiringMarket, MatchingMarket, Order
from pymaker.token import DSToken
from tests.helpers import wait_until_mock_called, is_hashable

PAST_BLOCKS = 100


class GeneralMarketTest:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.token1 = DSToken.deploy(self.web3, 'AAA')
        self.token1.mint(Wad.from_number(10000)).transact()
        self.token2 = DSToken.deploy(self.web3, 'BBB')
        self.token2.mint(Wad.from_number(10000)).transact()
        self.token3 = DSToken.deploy(self.web3, 'CCC')
        self.token3.mint(Wad.from_number(10000)).transact()
        self.otc = None

    def test_approve_and_make_and_getters(self):
        # given
        assert self.otc.get_last_order_id() == 0

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # then
        assert self.otc.get_last_order_id() == 1

        # and
        assert self.otc.get_order(1).order_id == 1
        assert self.otc.get_order(1).pay_token == self.token1.address
        assert self.otc.get_order(1).pay_amount == Wad.from_number(1)
        assert self.otc.get_order(1).buy_token == self.token2.address
        assert self.otc.get_order(1).buy_amount == Wad.from_number(2)
        assert self.otc.get_order(1).maker == self.our_address
        assert self.otc.get_order(1).timestamp != 0

        # and
        assert self.otc.get_orders() == [self.otc.get_order(1)]

    def test_get_orders_by_pair(self):
        # given
        self.otc.approve([self.token1, self.token2, self.token3], directly())

        # when
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(4)).transact()

        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(3)).transact()

        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token3.address, buy_amount=Wad.from_number(2)).transact()

        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token3.address, buy_amount=Wad.from_number(4)).transact()

        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token3.address, buy_amount=Wad.from_number(3)).transact()

        self.otc.make(pay_token=self.token2.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token3.address, buy_amount=Wad.from_number(2)).transact()

        self.otc.make(pay_token=self.token2.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token3.address, buy_amount=Wad.from_number(4)).transact()

        self.otc.make(pay_token=self.token2.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token3.address, buy_amount=Wad.from_number(3)).transact()

        self.otc.make(pay_token=self.token2.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token1.address, buy_amount=Wad.from_number(5)).transact()

        self.otc.make(pay_token=self.token2.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token1.address, buy_amount=Wad.from_number(6)).transact()

        # then
        def order_ids(orders: List[Order]) -> List[int]:
            return list(map(lambda order: order.order_id, orders))

        assert len(self.otc.get_orders()) == 11
        assert order_ids(self.otc.get_orders(self.token1.address, self.token2.address)) == [1, 2, 3]
        assert order_ids(self.otc.get_orders(self.token1.address, self.token3.address)) == [4, 5, 6]
        assert order_ids(self.otc.get_orders(self.token2.address, self.token3.address)) == [7, 8, 9]
        assert order_ids(self.otc.get_orders(self.token2.address, self.token1.address)) == [10, 11]

        # when
        self.otc.kill(8).transact()

        # then
        assert order_ids(self.otc.get_orders(self.token2.address, self.token3.address)) == [7, 9]

    def test_get_orders_by_maker(self):
        # given
        maker1 = self.our_address
        maker2 = Address(self.web3.eth.accounts[1])

        # and
        self.token1.transfer(maker2, Wad.from_number(500)).transact()

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # and
        self.web3.eth.defaultAccount = self.web3.eth.accounts[1]
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]

        # then
        assert len(self.otc.get_orders()) == 2
        assert len(self.otc.get_orders_by_maker(maker1)) == 1
        assert len(self.otc.get_orders_by_maker(maker2)) == 1

        # and
        assert self.otc.get_orders_by_maker(maker1)[0].maker == maker1
        assert self.otc.get_orders_by_maker(maker2)[0].maker == maker2

    def test_order_comparison(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # and
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(3),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(4)).transact()

        # then
        assert self.otc.get_last_order_id() == 2
        assert self.otc.get_order(1) == self.otc.get_order(1)
        assert self.otc.get_order(1) != self.otc.get_order(2)

    def test_order_hashable(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # expect
        assert is_hashable(self.otc.get_order(1))

    def test_take_partial(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # when
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.25)).transact()

        # then
        assert self.otc.get_order(1).pay_amount == Wad.from_number(0.75)
        assert self.otc.get_order(1).buy_amount == Wad.from_number(1.5)
        assert self.otc.get_orders() == [self.otc.get_order(1)]
        assert self.otc.get_last_order_id() == 1

    def test_take_complete(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # when
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(1)).transact()

        # then
        assert self.otc.get_order(1) is None
        assert self.otc.get_orders() == []
        assert self.otc.get_last_order_id() == 1

    def test_kill(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # when
        self.otc.kill(1).transact(gas=4000000)

        # then
        assert self.otc.get_order(1) is None
        assert self.otc.get_orders() == []
        assert self.otc.get_last_order_id() == 1

    def test_no_past_events_on_startup(self):
        assert self.otc.past_make(PAST_BLOCKS) == []
        assert self.otc.past_bump(PAST_BLOCKS) == []
        assert self.otc.past_take(PAST_BLOCKS) == []
        assert self.otc.past_kill(PAST_BLOCKS) == []

    def test_past_make(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # then
        past_make = self.otc.past_make(PAST_BLOCKS)
        assert len(past_make) == 1
        assert past_make[0].order_id == 1
        assert past_make[0].maker == self.our_address
        assert past_make[0].pay_token == self.token1.address
        assert past_make[0].pay_amount == Wad.from_number(1)
        assert past_make[0].buy_token == self.token2.address
        assert past_make[0].buy_amount == Wad.from_number(2)
        assert past_make[0].timestamp != 0
        assert past_make[0].raw['blockNumber'] > 0

    def test_past_bump(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()
        self.otc.bump(1).transact()

        # then
        past_bump = self.otc.past_bump(PAST_BLOCKS)
        assert len(past_bump) == 1
        assert past_bump[0].order_id == 1
        assert past_bump[0].maker == self.our_address
        assert past_bump[0].pay_token == self.token1.address
        assert past_bump[0].pay_amount == Wad.from_number(1)
        assert past_bump[0].buy_token == self.token2.address
        assert past_bump[0].buy_amount == Wad.from_number(2)
        assert past_bump[0].timestamp != 0
        assert past_bump[0].raw['blockNumber'] > 0

    def test_past_take(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # and
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.5)).transact()

        # then
        past_take = self.otc.past_take(PAST_BLOCKS)
        assert len(past_take) == 1
        assert past_take[0].order_id == 1
        assert past_take[0].maker == self.our_address
        assert past_take[0].taker == self.our_address
        assert past_take[0].pay_token == self.token1.address
        assert past_take[0].buy_token == self.token2.address
        assert past_take[0].take_amount == Wad.from_number(0.5)
        assert past_take[0].give_amount == Wad.from_number(1)
        assert past_take[0].timestamp != 0
        assert past_take[0].raw['blockNumber'] > 0

    def test_past_take_with_filter(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # and
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.5)).transact()

        # then
        assert len(self.otc.past_take(PAST_BLOCKS, {'maker': self.our_address.address})) == 1
        assert len(self.otc.past_take(PAST_BLOCKS, {'taker': self.our_address.address})) == 1
        assert len(self.otc.past_take(PAST_BLOCKS, {'maker': '0x0101010101020202020203030303030404040404'})) == 0
        assert len(self.otc.past_take(PAST_BLOCKS, {'taker': '0x0101010101020202020203030303030404040404'})) == 0

    def test_past_kill(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # and
        self.otc.kill(1).transact()

        # then
        past_kill = self.otc.past_kill(PAST_BLOCKS)
        assert len(past_kill) == 1
        assert past_kill[0].order_id == 1
        assert past_kill[0].maker == self.our_address
        assert past_kill[0].pay_token == self.token1.address
        assert past_kill[0].pay_amount == Wad.from_number(1)
        assert past_kill[0].buy_token == self.token2.address
        assert past_kill[0].buy_amount == Wad.from_number(2)
        assert past_kill[0].timestamp != 0
        assert past_kill[0].raw['blockNumber'] > 0

    @pytest.mark.timeout(10)
    def test_on_make(self):
        # given
        on_make_mock = Mock()
        self.otc.on_make(on_make_mock)

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # then
        on_make = wait_until_mock_called(on_make_mock)[0]
        assert on_make.order_id == 1
        assert on_make.maker == self.our_address
        assert on_make.pay_token == self.token1.address
        assert on_make.pay_amount == Wad.from_number(1)
        assert on_make.buy_token == self.token2.address
        assert on_make.buy_amount == Wad.from_number(2)
        assert on_make.timestamp != 0
        assert on_make.raw['blockNumber'] > 0

    @pytest.mark.timeout(10)
    def test_on_bump(self):
        # given
        on_bump_mock = Mock()
        self.otc.on_bump(on_bump_mock)

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()
        self.otc.bump(1).transact()

        # then
        on_bump = wait_until_mock_called(on_bump_mock)[0]
        assert on_bump.order_id == 1
        assert on_bump.maker == self.our_address
        assert on_bump.pay_token == self.token1.address
        assert on_bump.pay_amount == Wad.from_number(1)
        assert on_bump.buy_token == self.token2.address
        assert on_bump.buy_amount == Wad.from_number(2)
        assert on_bump.timestamp != 0
        assert on_bump.raw['blockNumber'] > 0

    @pytest.mark.timeout(10)
    def test_on_take(self):
        # given
        on_take_mock = Mock()
        self.otc.on_take(on_take_mock)

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # and
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.5)).transact()

        # then
        on_take = wait_until_mock_called(on_take_mock)[0]
        assert on_take.order_id == 1
        assert on_take.maker == self.our_address
        assert on_take.taker == self.our_address
        assert on_take.pay_token == self.token1.address
        assert on_take.buy_token == self.token2.address
        assert on_take.take_amount == Wad.from_number(0.5)
        assert on_take.give_amount == Wad.from_number(1)
        assert on_take.timestamp != 0
        assert on_take.raw['blockNumber'] > 0

    @pytest.mark.timeout(10)
    def test_on_take_wih_filter(self):
        # given
        on_take_filter1_mock = Mock()
        on_take_filter2_mock = Mock()
        self.otc.on_take(on_take_filter1_mock, {'maker': self.our_address.address})
        self.otc.on_take(on_take_filter2_mock, {'maker': '0x0101010101020202020201010101010303030303'})

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # and
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.5)).transact()

        # then
        assert len(wait_until_mock_called(on_take_filter1_mock)) == 1

        # and
        time.sleep(2)
        assert not on_take_filter2_mock.called

    @pytest.mark.timeout(10)
    def test_on_kill(self):
        # given
        on_kill_mock = Mock()
        self.otc.on_kill(on_kill_mock)

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # and
        self.otc.kill(1).transact()

        # then
        on_kill = wait_until_mock_called(on_kill_mock)[0]
        assert on_kill.order_id == 1
        assert on_kill.maker == self.our_address
        assert on_kill.pay_token == self.token1.address
        assert on_kill.pay_amount == Wad.from_number(1)
        assert on_kill.buy_token == self.token2.address
        assert on_kill.buy_amount == Wad.from_number(2)
        assert on_kill.timestamp != 0
        assert on_kill.raw['blockNumber'] > 0


class TestSimpleMarket(GeneralMarketTest):
    def setup_method(self):
        GeneralMarketTest.setup_method(self)
        self.otc = SimpleMarket.deploy(self.web3)

    def test_fail_when_no_contract_under_that_address(self):
        # expect
        with pytest.raises(Exception):
            SimpleMarket(web3=self.web3, address=Address('0xdeadadd1e5500000000000000000000000000000'))

    def test_should_have_printable_representation(self):
        assert repr(self.otc) == f"SimpleMarket('{self.otc.address}')"


class TestExpiringMarket(GeneralMarketTest):
    def setup_method(self):
        GeneralMarketTest.setup_method(self)
        self.otc = ExpiringMarket.deploy(self.web3, 2500000000)

    def test_fail_when_no_contract_under_that_address(self):
        # expect
        with pytest.raises(Exception):
            ExpiringMarket(web3=self.web3, address=Address('0xdeadadd1e5500000000000000000000000000000'))

    def test_is_closed(self):
        # when
        # (market is open)

        # then
        assert self.otc.is_closed() is False

        # when
        self.otc._contract.transact().stop()

        # then
        assert self.otc.is_closed() is True

    def test_should_have_printable_representation(self):
        assert repr(self.otc) == f"ExpiringMarket('{self.otc.address}')"


class TestMatchingMarket(GeneralMarketTest):
    def setup_method(self):
        GeneralMarketTest.setup_method(self)
        self.otc = MatchingMarket.deploy(self.web3, 2500000000)
        self.otc.add_token_pair_whitelist(self.token1.address, self.token2.address).transact()
        self.otc.add_token_pair_whitelist(self.token1.address, self.token3.address).transact()
        self.otc.add_token_pair_whitelist(self.token2.address, self.token3.address).transact()

    def test_fail_when_no_contract_under_that_address(self):
        # expect
        with pytest.raises(Exception):
            MatchingMarket(web3=self.web3, address=Address('0xdeadadd1e5500000000000000000000000000000'))

    def test_simple_matching(self):
        # given
        self.otc.approve([self.token1, self.token2], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # when
        self.otc.make(pay_token=self.token2.address, pay_amount=Wad.from_number(2.5),
                      buy_token=self.token1.address, buy_amount=Wad.from_number(1)).transact()

        # then
        assert self.otc.get_order(1) is None
        assert self.otc.get_order(2) is None

        # and
        assert self.otc.get_last_order_id() == 1

    def test_advanced_matching(self):
        # given
        self.otc.approve([self.token1, self.token2], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2.2)).transact()
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(1.8)).transact()
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2.1)).transact()
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(1.9)).transact()

        # when
        self.otc.make(pay_token=self.token2.address, pay_amount=Wad.from_number(20.1),
                      buy_token=self.token1.address, buy_amount=Wad.from_number(10)).transact(gas=4000000)

        # then
        assert self.otc.get_order(1) is None
        assert self.otc.get_order(2) is not None
        assert self.otc.get_order(3) is None
        assert self.otc.get_order(4) is not None
        assert self.otc.get_order(5) is None

        # and
        assert self.otc.get_last_order_id() == 6

        # and
        assert self.otc.get_order(6).order_id == 6
        assert self.otc.get_order(6).pay_token == self.token2.address
        assert self.otc.get_order(6).pay_amount == Wad.from_number(14.07)
        assert self.otc.get_order(6).buy_token == self.token1.address
        assert self.otc.get_order(6).buy_amount == Wad.from_number(7)
        assert self.otc.get_order(6).maker == self.our_address
        assert self.otc.get_order(6).timestamp != 0

    def test_should_have_printable_representation(self):
        assert repr(self.otc) == f"MatchingMarket('{self.otc.address}')"


class TestMatchingMarketPosition:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.token1 = DSToken.deploy(self.web3, 'AAA')
        self.token1.mint(Wad.from_number(10000)).transact()
        self.token2 = DSToken.deploy(self.web3, 'BBB')
        self.token2.mint(Wad.from_number(10000)).transact()
        self.otc = MatchingMarket.deploy(self.web3, 2500000000)
        self.otc.add_token_pair_whitelist(self.token1.address, self.token2.address).transact()
        self.otc.approve([self.token1, self.token2], directly())
        for amount in [11,55,44,34,36,21,45,51,15]:
            self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                          buy_token=self.token2.address, buy_amount=Wad.from_number(amount)).transact()

    def test_buy_enabled(self):
        # when
        self.otc.set_buy_enabled(False).transact()

        # then
        assert self.otc.is_buy_enabled() is False

        # when
        self.otc.set_buy_enabled(True).transact()

        # then
        assert self.otc.is_buy_enabled() is True

    def test_matching_enabled(self):
        # when
        self.otc.set_matching_enabled(False).transact()

        # then
        assert self.otc.is_matching_enabled() is False

        # when
        self.otc.set_matching_enabled(True).transact()

        # then
        assert self.otc.is_matching_enabled() is True

    def test_should_calculate_correct_order_position(self):
        # expect
        assert self.otc.position(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                                 buy_token=self.token2.address, buy_amount=Wad.from_number(35)) == 4

    def test_should_use_correct_order_position_by_default(self):
        # when
        explicit_position = self.otc.position(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                                              buy_token=self.token2.address, buy_amount=Wad.from_number(35))
        explicit_receipt = self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                                         buy_token=self.token2.address, buy_amount=Wad.from_number(35),
                                         pos=explicit_position).transact()
        explicit_gas_used = explicit_receipt.gas_used

        # and
        self.setup_method()
        implicit_receipt = self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                                         buy_token=self.token2.address, buy_amount=Wad.from_number(35)).transact()
        implicit_gas_used = implicit_receipt.gas_used

        # then
        assert explicit_gas_used == implicit_gas_used

    @pytest.mark.skip(reason="Stopped working as expected after recent `maker-otc` upgrade")
    def test_calculated_order_position_should_bring_gas_savings(self):
        # when
        position = self.otc.position(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                                     buy_token=self.token2.address, buy_amount=Wad.from_number(35))
        gas_used_optimal = self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                                         buy_token=self.token2.address, buy_amount=Wad.from_number(35),
                                         pos=position).transact().gas_used

        # and
        self.setup_method()
        gas_used_minus_1 = self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                                         buy_token=self.token2.address, buy_amount=Wad.from_number(35),
                                         pos=position-1).transact().gas_used

        # and
        self.setup_method()
        gas_used_plus_1 = self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                                        buy_token=self.token2.address, buy_amount=Wad.from_number(35),
                                        pos=position+1).transact().gas_used

        # then
        assert gas_used_optimal < gas_used_minus_1
        assert gas_used_optimal < gas_used_plus_1
