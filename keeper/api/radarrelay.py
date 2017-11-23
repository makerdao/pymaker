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

from pprint import pformat
from typing import List

import requests
from web3 import Web3

from keeper import ERC20Token, Wad
from keeper.api import Contract, Address


class Order:
    def __init__(self,
                 maker: Address,
                 taker: Address,
                 maker_fee: Wad,
                 taker_fee: Wad,
                 maker_token_amount: Wad,
                 taker_token_amount: Wad,
                 maker_token_address: Address,
                 taker_token_address: Address,
                 salt: int,
                 fee_recipient: Address,
                 expiration_unix_timestamp_sec: int,
                 exchange_contract_address: Address):

        assert(isinstance(maker, Address))
        assert(isinstance(taker, Address))
        assert(isinstance(maker_fee, Wad))
        assert(isinstance(taker_fee, Wad))
        assert(isinstance(maker_token_amount, Wad))
        assert(isinstance(taker_token_amount, Wad))
        assert(isinstance(maker_token_address, Address))
        assert(isinstance(taker_token_address, Address))
        assert(isinstance(salt, int))
        assert(isinstance(fee_recipient, Address))
        assert(isinstance(expiration_unix_timestamp_sec, int))
        assert(isinstance(exchange_contract_address, Address))

        self.maker = maker
        self.taker = taker
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.maker_token_amount = maker_token_amount
        self.taker_token_amount = taker_token_amount
        self.maker_token_address = maker_token_address
        self.taker_token_address = taker_token_address
        self.salt = salt
        self.fee_recipient = fee_recipient
        self.expiration_unix_timestamp_sec = expiration_unix_timestamp_sec
        self.exchange_contract_address = exchange_contract_address

    # @property
    # def sell_how_much(self):
    #     return self.amount_give
    #
    # @property
    # def buy_how_much(self):
    #     return self.amount_get

    @staticmethod
    def from_json(data: dict):
        assert(isinstance(data, dict))

        return Order(maker=Address(data['maker']),
                     taker=Address(data['taker']),
                     maker_fee=Wad(int(data['makerFee'])),
                     taker_fee=Wad(int(data['takerFee'])),
                     maker_token_amount=Wad(int(data['makerTokenAmount'])),
                     taker_token_amount=Wad(int(data['takerTokenAmount'])),
                     maker_token_address=Address(data['makerTokenAddress']),
                     taker_token_address=Address(data['takerTokenAddress']),
                     salt=int(data['salt']),
                     fee_recipient=Address(data['feeRecipient']),
                     expiration_unix_timestamp_sec=int(data['expirationUnixTimestampSec']),
                     exchange_contract_address=Address(data['exchangeContractAddress']))

    def to_json_without_fees(self) -> dict:
        return {
            "exchangeContractAddress": self.exchange_contract_address.address,
            "maker": self.maker.address,
            "taker": self.taker.address,
            "makerTokenAddress": self.maker_token_address.address,
            "takerTokenAddress": self.taker_token_address.address,
            "makerTokenAmount": str(self.maker_token_amount.value),
            "takerTokenAmount": str(self.taker_token_amount.value),
            "expirationUnixTimestampSec": str(self.expiration_unix_timestamp_sec),
            "salt": str(self.salt)
        }

    def __eq__(self, other):
        if isinstance(other, Order):
            return self.maker == other.maker and \
                   self.taker == other.taker and \
                   self.maker_fee == other.maker_fee and \
                   self.taker_fee == other.taker_fee and \
                   self.maker_token_amount == other.maker_token_amount and \
                   self.taker_token_amount == other.taker_token_amount and \
                   self.maker_token_address == other.maker_token_address and \
                   self.taker_token_address == other.taker_token_address and \
                   self.salt == other.salt and \
                   self.fee_recipient == other.fee_recipient and \
                   self.expiration_unix_timestamp_sec == other.expiration_unix_timestamp_sec and \
                   self.exchange_contract_address == other.exchange_contract_address
        else:
            return False

    def __hash__(self):
        return hash((self.maker,
                     self.taker,
                     self.maker_fee,
                     self.taker_fee,
                     self.maker_token_amount,
                     self.taker_token_amount,
                     self.maker_token_address,
                     self.taker_token_address,
                     self.salt,
                     self.fee_recipient,
                     self.expiration_unix_timestamp_sec,
                     self.exchange_contract_address))

    def __str__(self):
        return f"('{self.taker_token_address}', '{self.taker_token_amount}'," \
               f" '{self.maker_token_address}', '{self.maker_token_amount}'," \
               f" '{self.exchange_contract_address}', '{self.salt}')"

    def __repr__(self):
        return pformat(vars(self))


class RadarRelay(Contract):
    """A client for the RadarRelay/0x exchange contract.

    You can find the source code of the `0x` exchange contract here:
    <https://etherscan.io/address/0x12459c951127e0c374ff9105dda097662a027093#code.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the _0x_ `Exchange` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/Exchange.abi')
    bin = Contract._load_bin(__name__, 'abi/Exchange.bin')

    @staticmethod
    def deploy(web3: Web3,
               zrx_token: Address,
               token_transfer_proxy: Address):
        """Deploy a new instance of the `RadarRelay` contract.

        Args:
            web3: An instance of `Web` from `web3.py`.

        Returns:
            A `RadarRelay` class instance.
        """
        return RadarRelay(web3=web3,
                          address=Contract._deploy(web3, RadarRelay.abi, RadarRelay.bin, [
                              zrx_token.address,
                              token_transfer_proxy.address
                          ]))

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def zrx_token(self) -> Address:
        """Get the address of the ZRX token contract associated with this `Exchange` contract.

        Returns:
            The address of the `ZRX` token.
        """
        return Address(self._contract.call().ZRX_TOKEN_CONTRACT())

    def token_transfer_proxy(self) -> Address:
        """Get the address of the `TokenTransferProxy` contract associated with this `Exchange` contract.

        Returns:
            The address of the `TokenTransferProxy` token.
        """
        return Address(self._contract.call().TOKEN_TRANSFER_PROXY_CONTRACT())

    def approve(self, tokens: List[ERC20Token], approval_function):
        for token in tokens + [ERC20Token(web3=self.web3, address=self.zrx_token())]:
            approval_function(token, self.token_transfer_proxy(), '0x Exchange contract')

    def __repr__(self):
        return f"RadarRelay()"


class RadarRelayApi:
    """A client for the RadarRelay API. Following the Standard Relayer API V0.

    <https://radarrelay.com/standard-relayer-api>
    <https://github.com/0xProject/standard-relayer-api>

    Attributes:
        contract_address: Address of the 0x Exchange contract.
        api_server: Base URL of the Standard Relayer API server.
    """
    def __init__(self, contract_address: Address, api_server: str):
        assert(isinstance(contract_address, Address))
        assert(isinstance(api_server, str))

        self.contract_address = contract_address
        self.api_server = api_server

    def get_orders_by_maker(self, maker: Address):
        assert(isinstance(maker, Address))

        url = f"{self.api_server}/v0/orders?" \
              f"exchangeContractAddress={self.contract_address.address}&" \
              f"maker={maker.address}&" \
              f"per_page=100"

        response = requests.get(url).json()
        return list(map(lambda item: Order.from_json(item), response))

    def __repr__(self):
        return f"RadarRelayApi()"
