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

import copy
import random
from pprint import pformat
from typing import List, Optional

import array
import requests
from eth_utils import coerce_return_to_text, encode_hex
from web3 import Web3

from pymaker.token import ERC20Token
from pymaker.numeric import Wad
from pymaker.logger import Logger
from pymaker import Contract, Address, Transact
from pymaker.util import bytes_to_hexstring, hexstring_to_bytes


class Order:
    def __init__(self,
                 exchange,
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
                 expiration: int,
                 exchange_contract_address: Address,
                 ec_signature_r: Optional[str],
                 ec_signature_s: Optional[str],
                 ec_signature_v: Optional[int]):

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
        assert(isinstance(expiration, int))
        assert(isinstance(exchange_contract_address, Address))
        assert((isinstance(ec_signature_r, str) and isinstance(ec_signature_s, str) and isinstance(ec_signature_v, int))
               or (ec_signature_r is None and ec_signature_s is None and ec_signature_v is None))

        self._exchange = exchange
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
        self.expiration = expiration
        self.exchange_contract_address = exchange_contract_address
        self.ec_signature_r = ec_signature_r
        self.ec_signature_s = ec_signature_s
        self.ec_signature_v = ec_signature_v

    @property
    def sell_to_buy_price(self) -> Wad:
        return self.maker_token_amount / self.taker_token_amount

    @property
    def buy_to_sell_price(self) -> Wad:
        return self.taker_token_amount / self.maker_token_amount

    @property
    def remaining_sell_amount(self) -> Wad:
        return self.maker_token_amount - (self._exchange.get_unavailable_taker_token_amount(self)
                                          * self.maker_token_amount / self.taker_token_amount)

    @staticmethod
    def from_json(exchange, data: dict):
        assert(isinstance(data, dict))

        return Order(exchange=exchange,
                     maker=Address(data['maker']),
                     taker=Address(data['taker']),
                     maker_fee=Wad(int(data['makerFee'])),
                     taker_fee=Wad(int(data['takerFee'])),
                     maker_token_amount=Wad(int(data['makerTokenAmount'])),
                     taker_token_amount=Wad(int(data['takerTokenAmount'])),
                     maker_token_address=Address(data['makerTokenAddress']),
                     taker_token_address=Address(data['takerTokenAddress']),
                     salt=int(data['salt']),
                     fee_recipient=Address(data['feeRecipient']),
                     expiration=int(data['expirationUnixTimestampSec']),
                     exchange_contract_address=Address(data['exchangeContractAddress']),
                     ec_signature_r=data['ecSignature']['r'] if 'ecSignature' in data else None,
                     ec_signature_s=data['ecSignature']['s'] if 'ecSignature' in data else None,
                     ec_signature_v=data['ecSignature']['v'] if 'ecSignature' in data else None)

    def to_json_without_fees(self) -> dict:
        return {
            "exchangeContractAddress": self.exchange_contract_address.address,
            "maker": self.maker.address,
            "taker": self.taker.address,
            "makerTokenAddress": self.maker_token_address.address,
            "takerTokenAddress": self.taker_token_address.address,
            "makerTokenAmount": str(self.maker_token_amount.value),
            "takerTokenAmount": str(self.taker_token_amount.value),
            "expirationUnixTimestampSec": str(self.expiration),
            "salt": str(self.salt)
        }

    def to_json(self) -> dict:
        return {
            "exchangeContractAddress": self.exchange_contract_address.address,
            "maker": self.maker.address,
            "taker": self.taker.address,
            "makerTokenAddress": self.maker_token_address.address,
            "takerTokenAddress": self.taker_token_address.address,
            "feeRecipient": self.fee_recipient.address,
            "makerTokenAmount": str(self.maker_token_amount.value),
            "takerTokenAmount": str(self.taker_token_amount.value),
            "makerFee": str(self.maker_fee.value),
            "takerFee": str(self.taker_fee.value),
            "expirationUnixTimestampSec": str(self.expiration),
            "salt": str(self.salt),
            "ecSignature": {
                "r": self.ec_signature_r,
                "s": self.ec_signature_s,
                "v": self.ec_signature_v
            }
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
                   self.expiration == other.expiration and \
                   self.exchange_contract_address == other.exchange_contract_address and \
                   self.ec_signature_r == other.ec_signature_r and \
                   self.ec_signature_s == other.ec_signature_s and \
                   self.ec_signature_v == other.ec_signature_v
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
                     self.expiration,
                     self.exchange_contract_address,
                     self.ec_signature_r,
                     self.ec_signature_s,
                     self.ec_signature_v))

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

    _ZERO_ADDRESS = Address("0x0000000000000000000000000000000000000000")

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

    def create_order(self,
                     maker_token_amount: Wad,
                     taker_token_amount: Wad,
                     maker_token_address: Address,
                     taker_token_address: Address,
                     expiration: int):
        assert(isinstance(maker_token_amount, Wad))
        assert(isinstance(taker_token_amount, Wad))
        assert(isinstance(maker_token_address, Address))
        assert(isinstance(taker_token_address, Address))
        assert(isinstance(expiration, int))

        return Order(exchange=self,
                     maker=Address(self.web3.eth.defaultAccount),
                     taker=self._ZERO_ADDRESS,
                     maker_fee=Wad(0),
                     taker_fee=Wad(0),
                     maker_token_amount=maker_token_amount,
                     taker_token_amount=taker_token_amount,
                     maker_token_address=maker_token_address,
                     taker_token_address=taker_token_address,
                     salt=self.random_salt(),
                     fee_recipient=self._ZERO_ADDRESS,
                     expiration=expiration,
                     exchange_contract_address=self.address,
                     ec_signature_r=None,
                     ec_signature_s=None,
                     ec_signature_v=None)

    def get_order_hash(self, order: Order) -> str:
        assert(isinstance(order, Order))

        # the hash depends on the exchange contract address as well
        assert(order.exchange_contract_address == self.address)

        result = self._contract.call().getOrderHash(self._order_addresses(order), self._order_values(order))
        return bytes_to_hexstring(array.array('B', [ord(x) for x in result]).tobytes())

    def get_unavailable_taker_token_amount(self, order: Order) -> Wad:
        assert(isinstance(order, Order))

        return Wad(self._contract.call().getUnavailableTakerTokenAmount(hexstring_to_bytes(self.get_order_hash(order))))

    def sign_order(self, order: Order) -> Order:
        assert(isinstance(order, Order))

        # TODO duplicate code below
        signed_hash = self._eth_sign(self.web3.eth.defaultAccount, hexstring_to_bytes(self.get_order_hash(order)))[2:]
        r = bytes.fromhex(signed_hash[0:64])
        s = bytes.fromhex(signed_hash[64:128])
        v = ord(bytes.fromhex(signed_hash[128:130]))

        signed_order = copy.copy(order)
        signed_order.ec_signature_r = bytes_to_hexstring(r)
        signed_order.ec_signature_s = bytes_to_hexstring(s)
        signed_order.ec_signature_v = v
        return signed_order

    def cancel_order(self, order: Order) -> Transact:
        assert(isinstance(order, Order))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'cancelOrder',
                        [self._order_addresses(order), self._order_values(order), order.taker_token_amount.value])

    @staticmethod
    def _order_values(order):
        return [order.maker_token_amount.value,
                order.taker_token_amount.value,
                order.maker_fee.value,
                order.taker_fee.value,
                order.expiration,
                order.salt]

    @staticmethod
    def _order_addresses(order):
        return [order.maker.address,
                order.taker.address,
                order.maker_token_address.address,
                order.taker_token_address.address,
                order.fee_recipient.address]

    # TODO duplicate code below
    @coerce_return_to_text
    def _eth_sign(self, account, data_hash):
        return self.web3.manager.request_blocking(
            "eth_sign", [account, encode_hex(data_hash)],
        )

    @staticmethod
    def random_salt() -> int:
        return random.randint(1, 2**256 - 1)

    def __repr__(self):
        return f"RadarRelay()"


class RadarRelayApi:
    """A client for the RadarRelay API. Following the Standard Relayer API V0.

    <https://radarrelay.com/standard-relayer-api>
    <https://github.com/0xProject/standard-relayer-api>

    Attributes:
        exchange: The 0x Exchange contract.
        api_server: Base URL of the Standard Relayer API server.
        logger: Instance of the :py:class:`pymaker.Logger` class for event logging.
    """
    def __init__(self, exchange: RadarRelay, api_server: str, logger: Logger):
        assert(isinstance(exchange, RadarRelay))
        assert(isinstance(api_server, str))
        assert(isinstance(logger, Logger))

        self.exchange = exchange
        self.api_server = api_server
        self.logger = logger

    def get_orders_by_maker(self, maker: Address) -> List[Order]:
        assert(isinstance(maker, Address))

        url = f"{self.api_server}/v0/orders?" \
              f"exchangeContractAddress={self.exchange.address.address}&" \
              f"maker={maker.address}&" \
              f"per_page=10000"

        response = requests.get(url).json()
        return list(map(lambda item: Order.from_json(self.exchange, item), response))

    def calculate_fees(self, order: Order) -> Order:
        assert(isinstance(order, Order))

        response = requests.post(f"{self.api_server}/v0/fees", json=order.to_json_without_fees())
        if response.status_code == 200:
            data = response.json()

            order_with_fees = copy.copy(order)
            order_with_fees.maker_fee = Wad(int(data['makerFee']))
            order_with_fees.taker_fee = Wad(int(data['takerFee']))
            order_with_fees.fee_recipient = Address(data['feeRecipient'])
            return order_with_fees
        else:
            raise Exception(f"Failed to fetch fees for order: {response.text} ({response.status_code})")

    def submit_order(self, order: Order) -> bool:
        assert(isinstance(order, Order))

        response = requests.post(f"{self.api_server}/v0/order", json=order.to_json())
        if response.status_code == 201:
            self.logger.info(f"Placed 0x order: {order}")
            return True
        else:
            self.logger.warning(f"Failed to place 0x order: {response.text} ({response.status_code})")
            return False

    def __repr__(self):
        return f"RadarRelayApi()"
