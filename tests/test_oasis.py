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
from web3 import HTTPProvider
from web3 import Web3

from pymaker import Address, Wad, Contract
from pymaker.approval import directly
from pymaker.oasis import SimpleMarket, ExpiringMarket, MatchingMarket, Order
from pymaker.token import DSToken
from tests.helpers import wait_until_mock_called, is_hashable

PAST_BLOCKS = 100


class GeneralMarketTest:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
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

    def test_make_returns_new_order_ids(self):
        # given
        self.otc.approve([self.token1], directly())

        # expect
        for number in range(1, 10):
            receipt = self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                                    buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

            assert receipt.result == number
            assert self.otc.get_last_order_id() == number

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

    def test_remaining_sell_and_buy_amounts(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(pay_token=self.token1.address, pay_amount=Wad.from_number(1),
                      buy_token=self.token2.address, buy_amount=Wad.from_number(2)).transact()

        # and
        assert self.otc.get_order(1).remaining_sell_amount == Wad.from_number(1)
        assert self.otc.get_order(1).remaining_buy_amount == Wad.from_number(2)

        # when
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.25)).transact()

        # then
        assert self.otc.get_order(1).remaining_sell_amount == Wad.from_number(0.75)
        assert self.otc.get_order(1).remaining_buy_amount == Wad.from_number(1.5)

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


class TestMatchingMarketWithSupportContract(TestMatchingMarket):
    def setup_method(self):
        GeneralMarketTest.setup_method(self)

        support_abi = Contract._load_abi(__name__, '../pymaker/abi/MakerOtcSupportMethods.abi')
        support_bin = Contract._load_bin(__name__, '../pymaker/abi/MakerOtcSupportMethods.bin')
        support_address = Contract._deploy(self.web3, support_abi, support_bin, [])

        self.otc = MatchingMarket.deploy(self.web3, 2500000000, support_address)
        self.otc.add_token_pair_whitelist(self.token1.address, self.token2.address).transact()
        self.otc.add_token_pair_whitelist(self.token1.address, self.token3.address).transact()
        self.otc.add_token_pair_whitelist(self.token2.address, self.token3.address).transact()

    def test_fail_when_no_support_contract_under_that_address(self):
        # expect
        with pytest.raises(Exception):
            MatchingMarket(web3=self.web3,
                           address=self.otc.address,
                           support_address=Address('0xdeadadd1e5500000000000000000000000000000'))


class TestMatchingMarketPosition:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
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

    @pytest.mark.skip(reason="Works unreliably with ganache-cli")
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
