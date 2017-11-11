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

import hashlib
import json
import random
import sys
import threading
from pprint import pformat
from typing import Optional, List

import requests
from eth_abi.encoding import get_single_encoder
from eth_utils import coerce_return_to_text, encode_hex
from socketIO_client_nexus import SocketIO, LoggingNamespace
from web3 import Web3

from keeper.api import Contract, Address, Transact
from keeper.api import Logger
from keeper.api.numeric import Wad
from keeper.api.token import ERC20Token
from keeper.api.util import bytes_to_hexstring, hexstring_to_bytes


class Order:
    def __init__(self, token_get: Address, amount_get: Wad, token_give: Address, amount_give: Wad, expires: int):
        assert(isinstance(token_get, Address))
        assert(isinstance(amount_get, Wad))
        assert(isinstance(token_give, Address))
        assert(isinstance(amount_give, Wad))
        assert(isinstance(expires, int))

        self.token_get = token_get
        self.amount_get = amount_get
        self.token_give = token_give
        self.amount_give = amount_give
        self.expires = expires
        self.nonce = None
        self.user = None


class OffChainOrder(Order):
    def __init__(self, token_get: Address, amount_get: Wad, token_give: Address, amount_give: Wad, expires: int,
                 nonce: int, user: Address, v: int, r: bytes, s: bytes):
        super().__init__(token_get, amount_get, token_give, amount_give, expires)

        assert(isinstance(nonce, int))
        assert(isinstance(user, Address))
        assert(isinstance(v, int))
        assert(isinstance(r, bytes))
        assert(isinstance(s, bytes))

        self.nonce = nonce
        self.user = user
        self.v = v
        self.r = r
        self.s = s

    @staticmethod
    def from_json(data: dict):
        assert(isinstance(data, dict))
        return OffChainOrder(token_get=Address(data['tokenGet']),
                             amount_get=Wad(int(data['amountGet'])),
                             token_give=Address(data['tokenGive']),
                             amount_give=Wad(int(data['amountGive'])),
                             expires=int(data['expires']),
                             nonce=int(data['nonce']),
                             v=int(data['v']),
                             r=hexstring_to_bytes(data['r']),
                             s=hexstring_to_bytes(data['s']),
                             user=Address(data['user']))

    def to_json(self, etherdelta_contract_address: Address) -> dict:
        return {'contractAddr': etherdelta_contract_address.address,
                'tokenGet': self.token_get.address,
                'amountGet': self.amount_get.value,
                'tokenGive': self.token_give.address,
                'amountGive': self.amount_give.value,
                'expires': self.expires,
                'nonce': self.nonce,
                'v': self.v,
                'r': bytes_to_hexstring(self.r),
                's': bytes_to_hexstring(self.s),
                'user': self.user.address}

    def __eq__(self, other):
        if isinstance(other, OffChainOrder):
            return self.token_get == other.token_get and \
                   self.amount_get == other.amount_get and \
                   self.token_give == other.token_give and \
                   self.amount_give == other.amount_give and \
                   self.expires == other.expires and \
                   self.nonce == other.nonce and \
                   self.user == other.user and \
                   self.v == other.v and \
                   self.r == other.r and \
                   self.s == other.s
        else:
            return False

    def __hash__(self):
        return hash((self.token_get,
                     self.amount_get,
                     self.token_give,
                     self.amount_give,
                     self.expires,
                     self.nonce,
                     self.user,
                     self.v,
                     self.r,
                     self.s))

    def __repr__(self):
        return pformat(vars(self))


class OnChainOrder(Order):
    def __init__(self, token_get: Address, amount_get: Wad, token_give: Address, amount_give: Wad, expires: int,
                 nonce: int, user: Address):
        super().__init__(token_get, amount_get, token_give, amount_give, expires)

        assert(isinstance(nonce, int))
        assert(isinstance(user, Address))

        self.nonce = nonce
        self.user = user

    def __eq__(self, other):
        if isinstance(other, OnChainOrder):
            return self.token_get == other.token_get and \
                   self.amount_get == other.amount_get and \
                   self.token_give == other.token_give and \
                   self.amount_give == other.amount_give and \
                   self.expires == other.expires and \
                   self.nonce == other.nonce and \
                   self.user == other.user
        else:
            return False

    def __hash__(self):
        return hash((self.token_get,
                     self.amount_get,
                     self.token_give,
                     self.amount_give,
                     self.expires,
                     self.nonce,
                     self.user))

    def __repr__(self):
        return pformat(vars(self))


class LogOrder():
    def __init__(self, args):
        self.token_get = Address(args['tokenGet'])
        self.amount_get = Wad(args['amountGet'])
        self.token_give = Address(args['tokenGive'])
        self.amount_give = Wad(args['amountGive'])
        self.expires = args['expires']
        self.nonce = args['nonce']
        self.user = Address(args['user'])

    def to_order(self) -> OnChainOrder:
        return OnChainOrder(token_get=self.token_get,
                            amount_get=self.amount_get,
                            token_give=self.token_give,
                            amount_give=self.amount_give,
                            expires=self.expires,
                            nonce=self.nonce,
                            user=self.user)

    def __repr__(self):
        return pformat(vars(self))


class LogCancel():
    def __init__(self, args):
        self.token_get = Address(args['tokenGet'])
        self.amount_get = Wad(args['amountGet'])
        self.token_give = Address(args['tokenGive'])
        self.amount_give = Wad(args['amountGive'])
        self.expires = args['expires']
        self.nonce = args['nonce']
        self.user = Address(args['user'])
        self.v = args['v']
        self.r = args['r']
        self.s = args['s']

    def __repr__(self):
        return pformat(vars(self))


class EtherDelta(Contract):
    """A client for the EtherDelta exchange contract.

    You can find the source code of the `EtherDelta` contract here:
    <https://etherscan.io/address/0x8d12a197cb00d4747a1fe03395095ce2a5cc6819#code>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `EtherDelta` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/EtherDelta.abi')
    bin = Contract._load_bin(__name__, 'abi/EtherDelta.bin')

    ETH_TOKEN = Address('0x0000000000000000000000000000000000000000')

    @staticmethod
    def deploy(web3: Web3,
               admin: Address,
               fee_account: Address,
               account_levels_addr: Address,
               fee_make: Wad,
               fee_take: Wad,
               fee_rebate: Wad):
        """Deploy a new instance of the `EtherDelta` contract.

        Args:
            web3: An instance of `Web` from `web3.py`.

        Returns:
            A `EtherDelta` class instance.
        """
        return EtherDelta(web3=web3,
                          address=Contract._deploy(web3, EtherDelta.abi, EtherDelta.bin, [
                              admin.address,
                              fee_account.address,
                              account_levels_addr.address,
                              fee_make.value,
                              fee_take.value,
                              fee_rebate.value
                          ]))

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)
        self._onchain_orders = None
        self._offchain_orders = set()

    def approve(self, tokens: List[ERC20Token], approval_function):
        for token in tokens:
            approval_function(token, self.address, 'EtherDelta')

    def on_order(self, handler):
        self._on_event(self._contract, 'Order', LogOrder, handler)

    def on_cancel(self, handler):
        self._on_event(self._contract, 'Cancel', LogCancel, handler)

    def past_order(self, number_of_past_blocks: int) -> List[LogOrder]:
        return self._past_events(self._contract, 'Order', LogOrder, number_of_past_blocks)

    def past_cancel(self, number_of_past_blocks: int) -> List[LogCancel]:
        return self._past_events(self._contract, 'Cancel', LogCancel, number_of_past_blocks)

    def admin(self) -> Address:
        """Returns the address of the admin account.

        Returns:
            The address of the admin account.
        """
        return Address(self._contract.call().admin())

    def fee_account(self) -> Address:
        """Returns the address of the fee account i.e. the account that receives all fees collected.

        Returns:
            The address of the fee account.
        """
        return Address(self._contract.call().feeAccount())

    def account_levels_addr(self) -> Address:
        """Returns the address of the AccountLevels contract.

        Returns:
            The address of the AccountLevels contract.
        """
        return Address(self._contract.call().accountLevelsAddr())

    def fee_make(self) -> Wad:
        return Wad(self._contract.call().feeMake())

    def fee_take(self) -> Wad:
        return Wad(self._contract.call().feeTake())

    def fee_rebate(self) -> Wad:
        return Wad(self._contract.call().feeRebate())

    def deposit(self, amount: Wad) -> Transact:
        """Deposits `amount` of raw ETH to EtherDelta.

        Args:
            amount: Amount of raw ETH to be deposited on EtherDelta.

        Returns:
            A :py:class:`keeper.api.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(amount, Wad))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'deposit', [], {'value': amount.value})

    def withdraw(self, amount: Wad) -> Transact:
        """Withdraws `amount` of raw ETH from EtherDelta.

        The withdrawn ETH will get transferred to the calling account.

        Args:
            amount: Amount of raw ETH to be withdrawn from EtherDelta.

        Returns:
            A :py:class:`keeper.api.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(amount, Wad))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'withdraw', [amount.value])

    def balance_of(self, user: Address) -> Wad:
        """Returns the amount of raw ETH deposited by the specified user.

        Args:
            user: Address of the user to check the balance of.

        Returns:
            The raw ETH balance kept in the EtherDelta contract by the specified user.
        """
        assert(isinstance(user, Address))
        return Wad(self._contract.call().balanceOf('0x0000000000000000000000000000000000000000', user.address))

    def deposit_token(self, token: Address, amount: Wad) -> Transact:
        """Deposits `amount` of ERC20 token `token` to EtherDelta.

        Tokens will be pulled from the calling account, so the EtherDelta contract needs
        to have appropriate allowance. Either call `approve()` or set the allowance manually
        before trying to deposit tokens.

        Args:
            token: Address of the ERC20 token to be deposited.
            amount: Amount of token `token` to be deposited to EtherDelta.

        Returns:
            A :py:class:`keeper.api.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(token, Address))
        assert(isinstance(amount, Wad))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'depositToken',
                        [token.address, amount.value])

    def withdraw_token(self, token: Address, amount: Wad) -> Transact:
        """Withdraws `amount` of ERC20 token `token` from EtherDelta.

        Tokens will get transferred to the calling account.

        Args:
            token: Address of the ERC20 token to be withdrawn.
            amount: Amount of token `token` to be withdrawn from EtherDelta.

        Returns:
            A :py:class:`keeper.api.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(token, Address))
        assert(isinstance(amount, Wad))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'withdrawToken',
                        [token.address, amount.value])

    def balance_of_token(self, token: Address, user: Address) -> Wad:
        """Returns the amount of ERC20 token `token` deposited by the specified user.

        Args:
            token: Address of the ERC20 token return the balance of.
            user: Address of the user to check the balance of.

        Returns:
            The ERC20 token `token` balance kept in the EtherDelta contract by the specified user.
        """
        assert(isinstance(token, Address))
        assert(isinstance(user, Address))
        return Wad(self._contract.call().balanceOf(token.address, user.address))

    def active_onchain_orders(self) -> List[OnChainOrder]:
        # if this method is being called for the first time, discover existing orders
        # by looking for past events and set up monitoring of the future ones
        if self._onchain_orders is None:
            self._onchain_orders = set()
            self.on_order(lambda order: self._onchain_orders.add(order.to_order()))
            for old_order in self.past_order(1000000):
                self._onchain_orders.add(old_order.to_order())

        self._remove_filled_orders(self._onchain_orders)

        return list(self._onchain_orders)

    def _remove_filled_orders(self, order_set: set):
        assert(isinstance(order_set, set))

        # remove orders which have been completely filled (or cancelled)
        for order in list(order_set):
            if self.amount_filled(order) == order.amount_get:
                order_set.remove(order)

    def place_onchain_order(self,
                            token_get: Address,
                            amount_get: Wad,
                            token_give: Address,
                            amount_give: Wad,
                            expires: int) -> Transact:
        """Creates a new on-chain order.

        Although it's not necessary to have any amount of `token_give` deposited to EtherDelta
        before placing an order, nobody will be able to take this order until some balance of
        'token_give' is provided.

        If you want to trade raw ETH, pass `Address('0x0000000000000000000000000000000000000000')`
        as either `token_get` or `token_give`.

        Args:
            token_get: Address of the ERC20 token you want to be paid with.
            amount_get:  Amount of the `token_get` you want to receive.
            token_give: Address of the ERC20 token you want to put on sale.
            amount_give: Amount of the `token_give` token you want to put on sale.
            expires: The block number after which the order will expire.

        Returns:
            A :py:class:`keeper.api.Transact` instance, which can be used to trigger the transaction.
        """
        nonce = self.random_nonce()
        result = Transact(self, self.web3, self.abi, self.address, self._contract, 'order',
                          [token_get.address, amount_get.value, token_give.address, amount_give.value, expires, nonce])

        # in order to avoid delay between order creation and the Order event,
        # which would cause `active_orders()` to return a stale list,
        # we add newly created order to that collection straight away
        #
        # as the collection is a set, if the event arrives later,
        # no duplicate will get added
        if self._onchain_orders is not None:
            onchain_order = OnChainOrder(token_get, amount_get, token_give, amount_give,
                                         expires, nonce, Address(self.web3.eth.defaultAccount))

            # TODO we shouldn't actually do it if we do not know the transaction went through
            self._onchain_orders.add(onchain_order)

        return result

    def create_offchain_order(self,
                              token_get: Address,
                              amount_get: Wad,
                              token_give: Address,
                              amount_give: Wad,
                              expires: int) -> Optional[OffChainOrder]:
        """Creates a new off-chain order.

        Although it's not necessary to have any amount of `token_give` deposited to EtherDelta
        before placing an order, nobody will be able to take this order until some balance of
        'token_give' is provided.

        If you want to trade raw ETH, pass `Address('0x0000000000000000000000000000000000000000')`
        as either `token_get` or `token_give`.

        Args:
            token_get: Address of the ERC20 token you want to be paid with.
            amount_get:  Amount of the `token_get` you want to receive.
            token_give: Address of the ERC20 token you want to put on sale.
            amount_give: Amount of the `token_give` token you want to put on sale.
            expires: The block number after which the order will expire.

        Returns:
            Newly created order as an instance of the `OffChainOrder` class.
        """

        def encode_address(address: Address) -> bytes:
            return get_single_encoder("address", None, None)(address.address)[12:]

        def encode_uint256(value: int) -> bytes:
            return get_single_encoder("uint", 256, None)(value)

        nonce = self.random_nonce()
        order_hash = hashlib.sha256(encode_address(self.address) +
                                    encode_address(token_get) +
                                    encode_uint256(amount_get.value) +
                                    encode_address(token_give) +
                                    encode_uint256(amount_give.value) +
                                    encode_uint256(expires) +
                                    encode_uint256(nonce)).digest()
        signed_hash = self._eth_sign(self.web3.eth.defaultAccount, order_hash)[2:]
        r = bytes.fromhex(signed_hash[0:64])
        s = bytes.fromhex(signed_hash[64:128])
        v = ord(bytes.fromhex(signed_hash[128:130]))

        return OffChainOrder(token_get, amount_get, token_give, amount_give, expires, nonce,
                             Address(self.web3.eth.defaultAccount), v, r, s)

    def amount_available(self, order: Order) -> Wad:
        """Returns the amount that is still available (tradeable) for an order.

        The result will never be greater than `order.amount_get - amount_filled(order)`.
        It can be lower though if the order maker does not have enough balance on EtherDelta.

        Args:
            order: The order object you want to know the available amount of.
                Can be either an `OnChainOrder` or an `OffChainOrder`.

        Returns:
            The available amount for the order, in terms of `token_get`.
        """
        return Wad(self._contract.call().availableVolume(order.token_get.address,
                                                         order.amount_get.value,
                                                         order.token_give.address,
                                                         order.amount_give.value,
                                                         order.expires,
                                                         order.nonce,
                                                         order.user.address,
                                                         order.v if hasattr(order, 'v') else 0,
                                                         order.r if hasattr(order, 'r') else bytes(),
                                                         order.s if hasattr(order, 's') else bytes()))

    def amount_filled(self, order: Order) -> Wad:
        """Returns the amount that has been already filled for an order.

        The result will never be greater than `order.amount_get`. It can be lower though
        if the order maker does not have enough balance on EtherDelta.

        If an order has been cancelled, `amount_filled(order)` will be always equal
        to `order.amount_get`. Cancelled orders basically look like completely filled ones.

        Args:
            order: The order object you want to know the filled amount of.
                Can be either an `OnChainOrder` or an `OffChainOrder`.

        Returns:
            The amount already filled for the order, in terms of `token_get`.
        """
        return Wad(self._contract.call().amountFilled(order.token_get.address,
                                                      order.amount_get.value,
                                                      order.token_give.address,
                                                      order.amount_give.value,
                                                      order.expires,
                                                      order.nonce,
                                                      order.user.address,
                                                      order.v if hasattr(order, 'v') else 0,
                                                      order.r if hasattr(order, 'r') else bytes(),
                                                      order.s if hasattr(order, 's') else bytes()))

    def trade(self, order: Order, amount: Wad) -> Transact:
        """Takes (buys) an order.

        `amount` is in `token_get` terms, it is the amount you want to buy with. It can not be higher
        than `amount_available(order)`.

        The 'amount' of `token_get` tokens will get deducted from your EtherDelta balance if the trade was
        successful. The corresponding amount of `token_have` tokens will be added to your EtherDelta balance.

        Args:
            order: The order you want to take (buy). Can be either an `OnChainOrder` or an `OffChainOrder`.
            amount: Amount of `token_get` tokens that you want to be deducted from your EtherDelta balance
                in order to buy a corresponding amount of `token_have` tokens.

        Returns:
            A :py:class:`keeper.api.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(order, Order))
        assert(isinstance(amount, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'trade',
                        [order.token_get.address,
                         order.amount_get.value,
                         order.token_give.address,
                         order.amount_give.value,
                         order.expires,
                         order.nonce,
                         order.user.address,
                         order.v if hasattr(order, 'v') else 0,
                         order.r if hasattr(order, 'r') else bytes(),
                         order.s if hasattr(order, 's') else bytes(),
                         amount.value])

    def can_trade(self, order: Order, amount: Wad) -> bool:
        """Verifies whether a trade can be executed.

        Verifies whether amount `amount` can be traded on order `order` i.e. whether the `trade()`
        method executed with exactly the same parameters should succeed.

        Args:
            order: The order you want to verify the trade for. Can be either an `OnChainOrder` or an `OffChainOrder`.
            amount: Amount expressed in terms of `token_get` that you want to verify the trade for.

        Returns:
            'True' if the given amount can be traded on this order. `False` otherwise.
        """
        assert(isinstance(order, Order))
        assert(isinstance(amount, Wad))

        return self._contract.call().testTrade(order.token_get.address,
                                               order.amount_get.value,
                                               order.token_give.address,
                                               order.amount_give.value,
                                               order.expires,
                                               order.nonce,
                                               order.user.address,
                                               order.v if hasattr(order, 'v') else 0,
                                               order.r if hasattr(order, 'r') else bytes(),
                                               order.s if hasattr(order, 's') else bytes(),
                                               amount.value,
                                               self.web3.eth.defaultAccount)

    def cancel_order(self, order: Order) -> Transact:
        """Cancels an existing order.

        Orders can be cancelled only by their owners.

        Args:
            order: The order you want to cancel. Can be either an `OnChainOrder` or an `OffChainOrder`.

        Returns:
            A :py:class:`keeper.api.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(order, Order))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'cancelOrder',
                        [order.token_get.address,
                         order.amount_get.value,
                         order.token_give.address,
                         order.amount_give.value,
                         order.expires,
                         order.nonce,
                         order.v if hasattr(order, 'v') else 0,
                         order.r if hasattr(order, 'r') else bytes(),
                         order.s if hasattr(order, 's') else bytes()])

    @staticmethod
    def random_nonce():
        return random.randint(1, 2**32 - 1)

    @coerce_return_to_text
    def _eth_sign(self, account, data_hash):
        return self.web3.manager.request_blocking(
            "eth_sign", [account, encode_hex(data_hash)],
        )

    def __repr__(self):
        return f"EtherDelta('{self.address}')"


class EtherDeltaApi:
    """A client for the EtherDelta API backend.

    Attributes:
        contract_address: Address of the EtherDelta contract.
        api_server: Base URL of the EtherDelta API backend server.
        logger: Instance of the :py:class:`keeper.api.Logger` class for event logging.
    """
    def __init__(self, contract_address: Address, api_server: str, logger: Logger):
        assert(isinstance(contract_address, Address))
        assert(isinstance(api_server, str))
        assert(isinstance(logger, Logger))

        self.contract_address = contract_address
        self.api_server = api_server
        self.logger = logger
        self.socket_io = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while True:
            try:
                self.socket_io = SocketIO('https://socket.etherdelta.com', transports=['websocket', 'xhr-polling'])
                self.socket_io.on('connect', self._on_connect)
                self.socket_io.on('disconnect', self._on_disconnect)
                self.socket_io.on('reconnect', self._on_reconnect)
                self.socket_io.wait()
            except:
                self.logger.info("Multiple failures of the EtherDelta API, reinitializing it")

    def _on_connect(self):
        self.logger.info("Connected to the EtherDelta API")

    def _on_disconnect(self):
        self.logger.info("Disconnected from the EtherDelta API")

    def _on_reconnect(self):
        self.logger.info("Reconnected to the EtherDelta API")

    def publish_offchain_order(self, order: OffChainOrder) -> bool:
        assert(isinstance(order, OffChainOrder))

        if self.socket_io and self.socket_io.connected:
            self.logger.info(f"Publishing off-chain EtherDelta order ('{order.token_get}',"
                             f" '{order.amount_get}', '{order.token_give}', '{order.amount_give}', '{order.expires}',"
                             f" '{order.nonce}') in progress...")

            order_json = order.to_json(self.contract_address)
            self.logger.debug(json.dumps(order_json))
            self.socket_io.emit('message', order_json)
            return True
        else:
            self.logger.info(f"Failed to publish off-chain EtherDelta order as socketIO is not connected")
            return False

    def __repr__(self):
        return f"EtherDeltaApi()"
