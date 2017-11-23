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

import json

import pkg_resources
from web3 import EthereumTesterProvider
from web3 import Web3

from keeper import Wad
from keeper.api import Address
from keeper.api.approval import directly
from keeper.api.radarrelay import RadarRelay, Order
from keeper.api.token import DSToken, ERC20Token
from tests.api.helpers import is_hashable


class TestRadarRelay:
    #TODO duplicate of the deploy method in conftest.py
    def deploy(self, web3, contract_name, args=None):
        contract_factory = web3.eth.contract(abi=json.loads(pkg_resources.resource_string('keeper.api.feed', f'abi/{contract_name}.abi')),
                                             bytecode=pkg_resources.resource_string('keeper.api.feed', f'abi/{contract_name}.bin'))
        tx_hash = contract_factory.deploy(args=args)
        receipt = web3.eth.getTransactionReceipt(tx_hash)
        return receipt['contractAddress']

    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.zrx_token = ERC20Token(web3=self.web3, address=Address(self.deploy(self.web3, 'ZRXToken')))
        self.token_transfer_proxy_address = self.deploy(self.web3, 'TokenTransferProxy')
        self.radarrelay = RadarRelay.deploy(self.web3, self.zrx_token.address,
                                            Address(self.token_transfer_proxy_address))

    def test_correct_deployment(self):
        # expect
        assert self.radarrelay is not None
        assert self.radarrelay.address is not None
        assert self.radarrelay.zrx_token() == self.zrx_token.address
        assert self.radarrelay.token_transfer_proxy() == Address(self.token_transfer_proxy_address)

    def test_approval(self):
        # given
        token1 = DSToken.deploy(self.web3, 'AAA')
        token1.mint(Wad.from_number(100)).transact()

        # and
        assert token1.allowance_of(self.our_address, Address(self.token_transfer_proxy_address)) == Wad(0)
        assert self.zrx_token.allowance_of(self.our_address, Address(self.token_transfer_proxy_address)) == Wad(0)

        # when
        self.radarrelay.approve([token1], directly())

        # then
        assert token1.allowance_of(self.our_address, Address(self.token_transfer_proxy_address)) > Wad(0)
        assert self.zrx_token.allowance_of(self.our_address, Address(self.token_transfer_proxy_address)) > Wad(0)

    def test_should_have_printable_representation(self):
        assert repr(self.radarrelay) == f"RadarRelay()"


class TestOrder:
    def test_should_be_hashable(self):
        # given
        order = Order(maker=Address("0x9e56625509c2f60af937f23b7b532600390e8c8b"),
                      taker=Address("0x0000000000000000000000000000000000000000"),
                      maker_fee=Wad.from_number(123),
                      taker_fee=Wad.from_number(456),
                      maker_token_amount=Wad(10000000000000000),
                      taker_token_amount=Wad(20000000000000000),
                      maker_token_address=Address("0x323b5d4c32345ced77393b3530b1eed0f346429d"),
                      taker_token_address=Address("0xef7fff64389b814a946f3e92105513705ca6b990"),
                      salt=67006738228878699843088602623665307406148487219438534730168799356281242528500,
                      fee_recipient=Address('0x6666666666666666666666666666666666666666'),
                      expiration_unix_timestamp_sec=42,
                      exchange_contract_address=Address("0x12459c951127e0c374ff9105dda097662a027093"))

        # expect
        assert is_hashable(order)

    def test_parse_json_order(self):
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
        order = Order.from_json(json_order)

        # then
        assert order.exchange_contract_address == Address("0x12459c951127e0c374ff9105dda097662a027093")
        assert order.maker == Address("0x0046cac6668bef45b517a1b816a762f4f8add2a9")
        assert order.taker == Address("0x0000000000000000000000000000000000000000")
        assert order.maker_token_address == Address("0x59adcf176ed2f6788a41b8ea4c4904518e62b6a4")
        assert order.taker_token_address == Address("0x2956356cd2a2bf3202f771f50d3d14a367b48070")
        assert order.fee_recipient == Address("0xa258b39954cef5cb142fd567a46cddb31a670124")
        assert order.maker_token_amount == Wad.from_number(11)
        assert order.taker_token_amount == Wad.from_number(0.0308)
        assert order.maker_fee == Wad.from_number(0)
        assert order.taker_fee == Wad.from_number(0)
        assert order.expiration_unix_timestamp_sec == 1511988904
        assert order.salt == 50626048444772008084444062440502087868712695090943879708059561407114509847312

    def test_serialize_order_to_json_without_fees(self):
        # given
        order = Order(maker=Address("0x9e56625509c2f60af937f23b7b532600390e8c8b"),
                      taker=Address("0x0000000000000000000000000000000000000000"),
                      maker_fee=Wad.from_number(123),
                      taker_fee=Wad.from_number(456),
                      maker_token_amount=Wad(10000000000000000),
                      taker_token_amount=Wad(20000000000000000),
                      maker_token_address=Address("0x323b5d4c32345ced77393b3530b1eed0f346429d"),
                      taker_token_address=Address("0xef7fff64389b814a946f3e92105513705ca6b990"),
                      salt=67006738228878699843088602623665307406148487219438534730168799356281242528500,
                      fee_recipient=Address('0x6666666666666666666666666666666666666666'),
                      expiration_unix_timestamp_sec=42,
                      exchange_contract_address=Address("0x12459c951127e0c374ff9105dda097662a027093"))

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
