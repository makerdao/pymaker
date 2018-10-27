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

import json

import pkg_resources
import pytest
from mock import Mock
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.approval import directly
from pymaker.deployment import deploy_contract
from pymaker.numeric import Wad
from pymaker.token import DSToken, ERC20Token
from pymaker.zrx import ZrxExchange, Order, ZrxRelayerApi
from tests.helpers import is_hashable, wait_until_mock_called

PAST_BLOCKS = 100


class TestZrx:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.zrx_token = ERC20Token(web3=self.web3, address=deploy_contract(self.web3, 'ZRXToken'))
        self.token_transfer_proxy_address = deploy_contract(self.web3, 'TokenTransferProxy')
        self.exchange = ZrxExchange.deploy(self.web3, self.zrx_token.address, self.token_transfer_proxy_address)
        self.web3.eth.contract(abi=json.loads(pkg_resources.resource_string('pymaker.deployment', f'abi/TokenTransferProxy.abi')))(address=self.token_transfer_proxy_address.address).transact().addAuthorizedAddress(self.exchange.address.address)
        self.token1 = DSToken.deploy(self.web3, 'AAA')
        self.token1.mint(Wad.from_number(100)).transact()
        self.token2 = DSToken.deploy(self.web3, 'BBB')
        self.token2.mint(Wad.from_number(100)).transact()

    def test_fail_when_no_contract_under_that_address(self):
        # expect
        with pytest.raises(Exception):
            ZrxExchange(web3=self.web3, address=Address('0xdeadadd1e5500000000000000000000000000000'))

    def test_correct_deployment(self):
        # expect
        assert self.exchange is not None
        assert self.exchange.address is not None
        assert self.exchange.zrx_token() == self.zrx_token.address
        assert self.exchange.token_transfer_proxy() == self.token_transfer_proxy_address

    def test_approval(self):
        # given
        assert self.token1.allowance_of(self.our_address, self.token_transfer_proxy_address) == Wad(0)
        assert self.zrx_token.allowance_of(self.our_address, self.token_transfer_proxy_address) == Wad(0)

        # when
        self.exchange.approve([self.token1], directly())

        # then
        assert self.token1.allowance_of(self.our_address, self.token_transfer_proxy_address) > Wad(0)
        assert self.zrx_token.allowance_of(self.our_address, self.token_transfer_proxy_address) > Wad(0)

    def test_create_order(self):
        # when
        order = self.exchange.create_order(pay_token=Address("0x0202020202020202020202020202020202020202"),
                                           pay_amount=Wad.from_number(100),
                                           buy_token=Address("0x0101010101010101010101010101010101010101"),
                                           buy_amount=Wad.from_number(2.5), expiration=1763920792)

        # then
        assert order.maker == Address(self.web3.eth.defaultAccount)
        assert order.taker == Address("0x0000000000000000000000000000000000000000")
        assert order.pay_token == Address("0x0202020202020202020202020202020202020202")
        assert order.pay_amount == Wad.from_number(100)
        assert order.buy_token == Address("0x0101010101010101010101010101010101010101")
        assert order.buy_amount == Wad.from_number(2.5)
        assert order.salt >= 0
        assert order.expiration == 1763920792
        assert order.exchange_contract_address == self.exchange.address

        # and
        # [fees should be zero by default]
        assert order.maker_fee == Wad.from_number(0)
        assert order.taker_fee == Wad.from_number(0)
        assert order.fee_recipient == Address("0x0000000000000000000000000000000000000000")

    def test_get_order_hash(self):
        # given
        order = self.exchange.create_order(pay_token=Address("0x0202020202020202020202020202020202020202"),
                                           pay_amount=Wad.from_number(100),
                                           buy_token=Address("0x0101010101010101010101010101010101010101"),
                                           buy_amount=Wad.from_number(2.5), expiration=1763920792)

        # when
        order_hash = self.exchange.get_order_hash(order)

        # then
        assert order_hash.startswith('0x')
        assert len(order_hash) == 66

    def test_sign_order(self):
        # given
        order = self.exchange.create_order(pay_token=Address("0x0202020202020202020202020202020202020202"),
                                           pay_amount=Wad.from_number(100),
                                           buy_token=Address("0x0101010101010101010101010101010101010101"),
                                           buy_amount=Wad.from_number(2.5), expiration=1763920792)

        # when
        signed_order = self.exchange.sign_order(order)

        # then
        assert signed_order.ec_signature_r.startswith('0x')
        assert len(signed_order.ec_signature_r) == 66
        assert signed_order.ec_signature_s.startswith('0x')
        assert len(signed_order.ec_signature_s) == 66
        assert signed_order.ec_signature_v in [27, 28]

    def test_cancel_order(self):
        # given
        self.exchange.approve([self.token1, self.token2], directly())

        # when
        order = self.exchange.create_order(pay_token=self.token1.address, pay_amount=Wad.from_number(10),
                                           buy_token=self.token2.address, buy_amount=Wad.from_number(4),
                                           expiration=1763920792)
        # and
        signed_order = self.exchange.sign_order(order)

        # then
        assert self.exchange.get_unavailable_buy_amount(signed_order) == Wad(0)

        # when
        self.exchange.cancel_order(signed_order).transact()

        # then
        assert self.exchange.get_unavailable_buy_amount(signed_order) == Wad.from_number(4)

    def test_fill_order(self):
        # given
        self.exchange.approve([self.token1, self.token2], directly())

        # when
        order = self.exchange.create_order(pay_token=self.token1.address, pay_amount=Wad.from_number(10),
                                           buy_token=self.token2.address, buy_amount=Wad.from_number(4),
                                           expiration=1763920792)
        # and
        signed_order = self.exchange.sign_order(order)

        # then
        assert self.exchange.get_unavailable_buy_amount(signed_order) == Wad(0)

        # when
        self.exchange.fill_order(signed_order, Wad.from_number(3.5)).transact()

        # then
        assert self.exchange.get_unavailable_buy_amount(signed_order) == Wad.from_number(3.5)

    def test_remaining_buy_amount_and_remaining_sell_amount(self):
        # given
        self.exchange.approve([self.token1, self.token2], directly())

        # when
        order = self.exchange.create_order(pay_token=self.token1.address, pay_amount=Wad.from_number(10),
                                           buy_token=self.token2.address, buy_amount=Wad.from_number(4),
                                           expiration=1763920792)
        # and
        signed_order = self.exchange.sign_order(order)

        # then
        assert signed_order.remaining_sell_amount == Wad.from_number(10)
        assert signed_order.remaining_buy_amount == Wad.from_number(4)

        # when
        self.exchange.fill_order(signed_order, Wad.from_number(3.5)).transact()

        # then
        assert signed_order.remaining_sell_amount == Wad.from_number(1.25)
        assert signed_order.remaining_buy_amount == Wad.from_number(0.5)

    def test_past_fill(self):
        # given
        self.exchange.approve([self.token1, self.token2], directly())

        # when
        order = self.exchange.create_order(pay_token=self.token1.address, pay_amount=Wad.from_number(10),
                                           buy_token=self.token2.address, buy_amount=Wad.from_number(4),
                                           expiration=1763920792)
        # and
        self.exchange.fill_order(self.exchange.sign_order(order), Wad.from_number(3)).transact()

        # then
        past_fill = self.exchange.past_fill(PAST_BLOCKS)
        assert len(past_fill) == 1
        assert past_fill[0].maker == self.our_address
        assert past_fill[0].taker == self.our_address
        assert past_fill[0].fee_recipient == Address("0x0000000000000000000000000000000000000000")
        assert past_fill[0].pay_token == self.token1.address
        assert past_fill[0].buy_token == self.token2.address
        assert past_fill[0].filled_pay_amount == Wad.from_number(7.5)
        assert past_fill[0].filled_buy_amount == Wad.from_number(3)
        assert past_fill[0].paid_maker_fee == Wad.from_number(0)
        assert past_fill[0].paid_taker_fee == Wad.from_number(0)
        assert past_fill[0].tokens.startswith('0x')
        assert past_fill[0].order_hash == self.exchange.get_order_hash(self.exchange.sign_order(order))
        assert past_fill[0].raw['blockNumber'] > 0

    def test_past_cancel(self):
        # given
        self.exchange.approve([self.token1, self.token2], directly())

        # when
        order = self.exchange.create_order(pay_token=self.token1.address, pay_amount=Wad.from_number(10),
                                           buy_token=self.token2.address, buy_amount=Wad.from_number(4),
                                           expiration=1763920792)
        # and
        self.exchange.cancel_order(self.exchange.sign_order(order)).transact()

        # then
        past_cancel = self.exchange.past_cancel(PAST_BLOCKS)
        assert len(past_cancel) == 1
        assert past_cancel[0].maker == self.our_address
        assert past_cancel[0].fee_recipient == Address("0x0000000000000000000000000000000000000000")
        assert past_cancel[0].pay_token == self.token1.address
        assert past_cancel[0].cancelled_pay_amount == Wad.from_number(10)
        assert past_cancel[0].buy_token == self.token2.address
        assert past_cancel[0].cancelled_buy_amount == Wad.from_number(4)
        assert past_cancel[0].tokens.startswith('0x')
        assert past_cancel[0].order_hash == self.exchange.get_order_hash(self.exchange.sign_order(order))
        assert past_cancel[0].raw['blockNumber'] > 0

    def test_should_have_printable_representation(self):
        assert repr(self.exchange) == f"ZrxExchange('{self.exchange.address}')"


class TestOrder:
    def test_should_be_comparable(self):
        # given
        order1 = Order(exchange=None,
                       maker=Address("0x9e56625509c2f60af937f23b7b532600390e8c8b"),
                       taker=Address("0x0000000000000000000000000000000000000000"),
                       maker_fee=Wad.from_number(123),
                       taker_fee=Wad.from_number(456),
                       pay_token=Address("0x323b5d4c32345ced77393b3530b1eed0f346429d"),
                       pay_amount=Wad(10000000000000000),
                       buy_token=Address("0xef7fff64389b814a946f3e92105513705ca6b990"),
                       buy_amount=Wad(20000000000000000),
                       salt=67006738228878699843088602623665307406148487219438534730168799356281242528500,
                       fee_recipient=Address('0x6666666666666666666666666666666666666666'),
                       expiration=42,
                       exchange_contract_address=Address("0x12459c951127e0c374ff9105dda097662a027093"),
                       ec_signature_r="0xf9f6a3b67b52d40c16387df2cd6283bbdbfc174577743645dd6f4bd828c7dbc3",
                       ec_signature_s="0x15baf69f6c3cc8ac0f62c89264d73accf1ae165cce5d6e2a0b6325c6e4bab964",
                       ec_signature_v=28)

        order2 = Order(exchange=None,
                       maker=Address("0x9e56625509c2f60af937f23b7b532600390e8c8b"),
                       taker=Address("0x0000000000000000000000000000000000000000"),
                       maker_fee=Wad.from_number(123),
                       taker_fee=Wad.from_number(456),
                       pay_token=Address("0x323b5d4c32345ced77393b3530b1eed0f346429d"),
                       pay_amount=Wad(10000000000000000),
                       buy_token=Address("0xef7fff64389b814a946f3e92105513705ca6b990"),
                       buy_amount=Wad(20000000000000000),
                       salt=67006738228878699843088602623665307406148487219438534730168799356281242528500,
                       fee_recipient=Address('0x6666666666666666666666666666666666666666'),
                       expiration=42,
                       exchange_contract_address=Address("0x12459c951127e0c374ff9105dda097662a027093"),
                       ec_signature_r="0xf9f6a3b67b52d40c16387df2cd6283bbdbfc174577743645dd6f4bd828c7dbc3",
                       ec_signature_s="0x15baf69f6c3cc8ac0f62c89264d73accf1ae165cce5d6e2a0b6325c6e4bab964",
                       ec_signature_v=28)

        # expect
        assert order1 == order2

        # when
        order2.maker_fee = Wad.from_number(124)

        # then
        assert order1 != order2

        # when
        order1.maker_fee = Wad.from_number(124)

        # then
        assert order1 == order2

    def test_should_be_hashable(self):
        # given
        order = Order(exchange=None,
                      maker=Address("0x9e56625509c2f60af937f23b7b532600390e8c8b"),
                      taker=Address("0x0000000000000000000000000000000000000000"),
                      maker_fee=Wad.from_number(123),
                      taker_fee=Wad.from_number(456),
                      pay_token=Address("0x323b5d4c32345ced77393b3530b1eed0f346429d"),
                      pay_amount=Wad(10000000000000000),
                      buy_token=Address("0xef7fff64389b814a946f3e92105513705ca6b990"),
                      buy_amount=Wad(20000000000000000),
                      salt=67006738228878699843088602623665307406148487219438534730168799356281242528500,
                      fee_recipient=Address('0x6666666666666666666666666666666666666666'),
                      expiration=42,
                      exchange_contract_address=Address("0x12459c951127e0c374ff9105dda097662a027093"),
                      ec_signature_r="0xf9f6a3b67b52d40c16387df2cd6283bbdbfc174577743645dd6f4bd828c7dbc3",
                      ec_signature_s="0x15baf69f6c3cc8ac0f62c89264d73accf1ae165cce5d6e2a0b6325c6e4bab964",
                      ec_signature_v=28)

        # expect
        assert is_hashable(order)

    def test_parse_signed_json_order(self):
        # given
        json_order = json.loads("""{
            "orderHash": "0x02266a4887256fdf16b47ca13e3f2cca76f93724842f3f7ddf55d92fb6601b6f",
            "exchangeContractAddress": "0x12459c951127e0c374ff9105dda097662a027093",
            "maker": "0x0046cac6668bef45b517a1b816a762f4f8add2a9",
            "taker": "0x0000000000000000000000000000000000000000",
            "makerTokenAddress": "0x59adcf176ed2f6788a41b8ea4c4904518e62b6a4",
            "takerTokenAddress": "0x2956356cd2a2bf3202f771f50d3d14a367b48070",
            "feeRecipient": "0xa258b39954cef5cb142fd567a46cddb31a670124",
            "makerTokenAmount": "11000000000000000000",
            "takerTokenAmount": "30800000000000000",
            "makerFee": "0",
            "takerFee": "0",
            "expirationUnixTimestampSec": "1511988904",
            "salt": "50626048444772008084444062440502087868712695090943879708059561407114509847312",
            "ecSignature": {
                "r": "0xf9f6a3b67b52d40c16387df2cd6283bbdbfc174577743645dd6f4bd828c7dbc3",
                "s": "0x15baf69f6c3cc8ac0f62c89264d73accf1ae165cce5d6e2a0b6325c6e4bab964",
                "v": 28
            }
        }""")

        # when
        order = Order.from_json(None, json_order)

        # then
        assert order.exchange_contract_address == Address("0x12459c951127e0c374ff9105dda097662a027093")
        assert order.maker == Address("0x0046cac6668bef45b517a1b816a762f4f8add2a9")
        assert order.taker == Address("0x0000000000000000000000000000000000000000")
        assert order.pay_token == Address("0x59adcf176ed2f6788a41b8ea4c4904518e62b6a4")
        assert order.buy_token == Address("0x2956356cd2a2bf3202f771f50d3d14a367b48070")
        assert order.fee_recipient == Address("0xa258b39954cef5cb142fd567a46cddb31a670124")
        assert order.pay_amount == Wad.from_number(11)
        assert order.buy_amount == Wad.from_number(0.0308)
        assert order.maker_fee == Wad.from_number(0)
        assert order.taker_fee == Wad.from_number(0)
        assert order.expiration == 1511988904
        assert order.salt == 50626048444772008084444062440502087868712695090943879708059561407114509847312
        assert order.ec_signature_r == "0xf9f6a3b67b52d40c16387df2cd6283bbdbfc174577743645dd6f4bd828c7dbc3"
        assert order.ec_signature_s == "0x15baf69f6c3cc8ac0f62c89264d73accf1ae165cce5d6e2a0b6325c6e4bab964"
        assert order.ec_signature_v == 28

    def test_parse_unsigned_json_order(self):
        # given
        json_order = json.loads("""{
            "orderHash": "0x02266a4887256fdf16b47ca13e3f2cca76f93724842f3f7ddf55d92fb6601b6f",
            "exchangeContractAddress": "0x12459c951127e0c374ff9105dda097662a027093",
            "maker": "0x0046cac6668bef45b517a1b816a762f4f8add2a9",
            "taker": "0x0000000000000000000000000000000000000000",
            "makerTokenAddress": "0x59adcf176ed2f6788a41b8ea4c4904518e62b6a4",
            "takerTokenAddress": "0x2956356cd2a2bf3202f771f50d3d14a367b48070",
            "feeRecipient": "0xa258b39954cef5cb142fd567a46cddb31a670124",
            "makerTokenAmount": "11000000000000000000",
            "takerTokenAmount": "30800000000000000",
            "makerFee": "0",
            "takerFee": "0",
            "expirationUnixTimestampSec": "1511988904",
            "salt": "50626048444772008084444062440502087868712695090943879708059561407114509847312"
        }""")

        # when
        order = Order.from_json(None, json_order)

        # then
        assert order.exchange_contract_address == Address("0x12459c951127e0c374ff9105dda097662a027093")
        assert order.maker == Address("0x0046cac6668bef45b517a1b816a762f4f8add2a9")
        assert order.taker == Address("0x0000000000000000000000000000000000000000")
        assert order.pay_token == Address("0x59adcf176ed2f6788a41b8ea4c4904518e62b6a4")
        assert order.buy_token == Address("0x2956356cd2a2bf3202f771f50d3d14a367b48070")
        assert order.fee_recipient == Address("0xa258b39954cef5cb142fd567a46cddb31a670124")
        assert order.pay_amount == Wad.from_number(11)
        assert order.buy_amount == Wad.from_number(0.0308)
        assert order.maker_fee == Wad.from_number(0)
        assert order.taker_fee == Wad.from_number(0)
        assert order.expiration == 1511988904
        assert order.salt == 50626048444772008084444062440502087868712695090943879708059561407114509847312
        assert order.ec_signature_r is None
        assert order.ec_signature_s is None
        assert order.ec_signature_v is None

    def test_serialize_order_to_json_without_fees(self):
        # given
        order = Order(exchange=None,
                      maker=Address("0x9e56625509c2f60af937f23b7b532600390e8c8b"),
                      taker=Address("0x0000000000000000000000000000000000000000"),
                      maker_fee=Wad.from_number(123),
                      taker_fee=Wad.from_number(456),
                      pay_token=Address("0x323b5d4c32345ced77393b3530b1eed0f346429d"),
                      pay_amount=Wad(10000000000000000),
                      buy_token=Address("0xef7fff64389b814a946f3e92105513705ca6b990"),
                      buy_amount=Wad(20000000000000000),
                      salt=67006738228878699843088602623665307406148487219438534730168799356281242528500,
                      fee_recipient=Address('0x6666666666666666666666666666666666666666'),
                      expiration=42,
                      exchange_contract_address=Address("0x12459c951127e0c374ff9105dda097662a027093"),
                      ec_signature_r="0xde21c90d3db3abdc8bdc5fafb1f5432a1dede4d621508e7d96fb2ebc15d7eb2f",
                      ec_signature_s="0x74f3cb421f75727b78ae98157ddce6a77b46c8714f5848d70f6da083527e1719",
                      ec_signature_v=28)

        # when
        json_order = order.to_json_without_fees()

        # then
        assert json_order == json.loads("""{
            "exchangeContractAddress": "0x12459c951127e0c374ff9105dda097662a027093",
            "maker": "0x9e56625509c2f60af937f23b7b532600390e8c8b",
            "taker": "0x0000000000000000000000000000000000000000",
            "makerTokenAddress": "0x323b5d4c32345ced77393b3530b1eed0f346429d",
            "takerTokenAddress": "0xef7fff64389b814a946f3e92105513705ca6b990",
            "makerTokenAmount": "10000000000000000",
            "takerTokenAmount": "20000000000000000",
            "expirationUnixTimestampSec": "42",
            "salt": "67006738228878699843088602623665307406148487219438534730168799356281242528500"
        }""")

    def test_serialize_order_to_json(self):
        # given
        order = Order(exchange=None,
                      maker=Address("0x9e56625509c2f60af937f23b7b532600390e8c8b"),
                      taker=Address("0x0000000000000000000000000000000000000000"),
                      maker_fee=Wad.from_number(123),
                      taker_fee=Wad.from_number(456),
                      pay_token=Address("0x323b5d4c32345ced77393b3530b1eed0f346429d"),
                      pay_amount=Wad(10000000000000000),
                      buy_token=Address("0xef7fff64389b814a946f3e92105513705ca6b990"),
                      buy_amount=Wad(20000000000000000),
                      salt=67006738228878699843088602623665307406148487219438534730168799356281242528500,
                      fee_recipient=Address('0x6666666666666666666666666666666666666666'),
                      expiration=42,
                      exchange_contract_address=Address("0x12459c951127e0c374ff9105dda097662a027093"),
                      ec_signature_r="0xde21c90d3db3abdc8bdc5fafb1f5432a1dede4d621508e7d96fb2ebc15d7eb2f",
                      ec_signature_s="0x74f3cb421f75727b78ae98157ddce6a77b46c8714f5848d70f6da083527e1719",
                      ec_signature_v=28)

        # when
        json_order = order.to_json()

        # then
        assert json_order == json.loads("""{
            "exchangeContractAddress": "0x12459c951127e0c374ff9105dda097662a027093",
            "maker": "0x9e56625509c2f60af937f23b7b532600390e8c8b",
            "taker": "0x0000000000000000000000000000000000000000",
            "makerTokenAddress": "0x323b5d4c32345ced77393b3530b1eed0f346429d",
            "takerTokenAddress": "0xef7fff64389b814a946f3e92105513705ca6b990",
            "feeRecipient": "0x6666666666666666666666666666666666666666",
            "makerTokenAmount": "10000000000000000",
            "takerTokenAmount": "20000000000000000",
            "makerFee": "123000000000000000000",
            "takerFee": "456000000000000000000",
            "expirationUnixTimestampSec": "42",
            "salt": "67006738228878699843088602623665307406148487219438534730168799356281242528500",
            "ecSignature": {
                "r": "0xde21c90d3db3abdc8bdc5fafb1f5432a1dede4d621508e7d96fb2ebc15d7eb2f",
                "s": "0x74f3cb421f75727b78ae98157ddce6a77b46c8714f5848d70f6da083527e1719",
                "v": 28
            }
        }""")
