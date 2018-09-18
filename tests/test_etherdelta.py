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

import pytest
from mock import Mock
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.approval import directly
from pymaker.etherdelta import EtherDelta, EtherDeltaApi
from pymaker.numeric import Wad
from pymaker.token import DSToken
from tests.helpers import is_hashable, wait_until_mock_called

PAST_BLOCKS = 100


class TestEtherDelta:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.etherdelta = EtherDelta.deploy(self.web3,
                                            admin=Address('0x1111100000999998888877777666665555544444'),
                                            fee_account=Address('0x8888877777666665555544444111110000099999'),
                                            account_levels_addr=Address('0x0000000000000000000000000000000000000000'),
                                            fee_make=Wad.from_number(0.01),
                                            fee_take=Wad.from_number(0.02),
                                            fee_rebate=Wad.from_number(0.03))
        self.token1 = DSToken.deploy(self.web3, 'AAA')
        self.token1.mint(Wad.from_number(100)).transact()
        self.token2 = DSToken.deploy(self.web3, 'BBB')
        self.token2.mint(Wad.from_number(100)).transact()

    def test_fail_when_no_contract_under_that_address(self):
        # expect
        with pytest.raises(Exception):
            EtherDelta(web3=self.web3, address=Address('0xdeadadd1e5500000000000000000000000000000'))

    def test_addresses(self):
        # expect
        assert self.etherdelta.admin() == Address('0x1111100000999998888877777666665555544444')
        assert self.etherdelta.fee_account() == Address('0x8888877777666665555544444111110000099999')
        assert self.etherdelta.account_levels_addr() == Address('0x0000000000000000000000000000000000000000')

    def test_fees(self):
        # expect
        assert self.etherdelta.fee_make() == Wad.from_number(0.01)
        assert self.etherdelta.fee_take() == Wad.from_number(0.02)
        assert self.etherdelta.fee_rebate() == Wad.from_number(0.03)

    def test_deposit_and_withdraw_eth(self):
        # when
        self.etherdelta.deposit(Wad.from_number(2.5)).transact()

        # then
        assert self.etherdelta.balance_of(self.our_address) == Wad.from_number(2.5)

        # when
        self.etherdelta.withdraw(Wad.from_number(1.1)).transact()

        # then
        assert self.etherdelta.balance_of(self.our_address) == Wad.from_number(1.4)

    def test_deposit_and_withdraw_token(self):
        # given
        self.etherdelta.approve([self.token1], directly())

        # when
        self.etherdelta.deposit_token(self.token1.address, Wad.from_number(1.5)).transact()

        # then
        assert self.etherdelta.balance_of_token(self.token1.address, self.our_address) == Wad.from_number(1.5)

        # when
        self.etherdelta.withdraw_token(self.token1.address, Wad.from_number(0.2)).transact()

        # then
        assert self.etherdelta.balance_of_token(self.token1.address, self.our_address) == Wad.from_number(1.3)

    def test_offchain_order_happy_path(self):
        # given
        self.etherdelta.approve([self.token1, self.token2], directly())
        self.etherdelta.deposit_token(self.token1.address, Wad.from_number(10)).transact()
        self.etherdelta.deposit_token(self.token2.address, Wad.from_number(10)).transact()

        # when
        order = self.etherdelta.create_order(pay_token=self.token1.address, pay_amount=Wad.from_number(2),
                                             buy_token=self.token2.address, buy_amount=Wad.from_number(4),
                                             expires=100000000)

        # then
        assert order.maker == self.our_address
        assert order.pay_token == self.token1.address
        assert order.pay_amount == Wad.from_number(2)
        assert order.buy_token == self.token2.address
        assert order.buy_amount == Wad.from_number(4)
        assert order.expires == 100000000

        # and
        assert self.etherdelta.amount_available(order) == Wad.from_number(4)
        assert self.etherdelta.amount_filled(order) == Wad.from_number(0)
        assert order.remaining_sell_amount == Wad.from_number(2)
        assert order.remaining_buy_amount == Wad.from_number(4)

        # and
        assert self.etherdelta.can_trade(order, Wad.from_number(1.5))
        assert not self.etherdelta.can_trade(order, Wad.from_number(5.5))

        # when
        self.etherdelta.trade(order, Wad.from_number(1.5)).transact()

        # then
        assert self.etherdelta.amount_available(order) == Wad.from_number(2.5)
        assert self.etherdelta.amount_filled(order) == Wad.from_number(1.5)
        assert order.remaining_sell_amount == Wad.from_number(1.25)
        assert order.remaining_buy_amount == Wad.from_number(2.5)

        # when
        self.etherdelta.withdraw_token(self.token1.address, Wad.from_number(9.3)).transact()

        # then
        assert self.etherdelta.amount_available(order) == Wad.from_number(1.4)
        assert self.etherdelta.amount_filled(order) == Wad.from_number(1.5)

        # when
        self.etherdelta.cancel_order(order).transact()

        # then
        assert self.etherdelta.amount_available(order) == Wad.from_number(0)
        assert self.etherdelta.amount_filled(order) == Wad.from_number(4)

    def test_no_past_events_on_startup(self):
        assert self.etherdelta.past_trade(PAST_BLOCKS) == []

    def test_past_take(self):
        # given
        self.etherdelta.approve([self.token1, self.token2], directly())
        self.etherdelta.deposit_token(self.token1.address, Wad.from_number(10)).transact()
        self.etherdelta.deposit_token(self.token2.address, Wad.from_number(10)).transact()

        # when
        order = self.etherdelta.create_order(pay_token=self.token1.address, pay_amount=Wad.from_number(2),
                                             buy_token=self.token2.address, buy_amount=Wad.from_number(4),
                                             expires=100000000)

        # and
        self.etherdelta.trade(order, Wad.from_number(1.5)).transact()

        # then
        past_trade = self.etherdelta.past_trade(PAST_BLOCKS)
        assert len(past_trade) == 1
        assert past_trade[0].maker == self.our_address
        assert past_trade[0].taker == self.our_address
        assert past_trade[0].pay_token == self.token1.address
        assert past_trade[0].buy_token == self.token2.address
        assert past_trade[0].take_amount == Wad.from_number(0.75)
        assert past_trade[0].give_amount == Wad.from_number(1.5)
        assert past_trade[0].raw['blockNumber'] > 0

    def test_order_comparison(self):
        # given
        order1 = self.etherdelta.create_order(pay_token=self.token1.address, pay_amount=Wad.from_number(2),
                                              buy_token=self.token2.address, buy_amount=Wad.from_number(4),
                                              expires=100000000)

        # and
        order2 = self.etherdelta.create_order(pay_token=self.token1.address, pay_amount=Wad.from_number(2),
                                              buy_token=self.token2.address, buy_amount=Wad.from_number(4),
                                              expires=100000000)

        # then
        assert order1 == order1
        assert order1 != order2  # even if both orders seem to be identical, they will have different
                                 # nonces generated so they are not the same order

    def test_order_hashable(self):
        # given
        order1 = self.etherdelta.create_order(pay_token=self.token1.address, pay_amount=Wad.from_number(2),
                                              buy_token=self.token2.address, buy_amount=Wad.from_number(4),
                                              expires=100000000)

        # expect
        assert is_hashable(order1)

    def test_should_have_printable_representation(self):
        assert repr(self.etherdelta) == f"EtherDelta('{self.etherdelta.address}')"


class TestEtherDeltaApi:
    def setup_method(self):
        self.etherdelta_api = EtherDeltaApi(client_tool_directory='some-dir',
                                            client_tool_command='some command',
                                            api_server='https://127.0.0.1:66666',
                                            number_of_attempts=1,
                                            retry_interval=15,
                                            timeout=90)

    def test_should_have_printable_representation(self):
        assert repr(self.etherdelta_api) == f"EtherDeltaApi()"
