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
import random
from typing import Optional, List

from eth_abi.encoding import get_single_encoder
from eth_utils import coerce_return_to_text, encode_hex
from web3 import Web3

from api import Contract, Address, Receipt
from api.numeric import Wad
from api.token import ERC20Token


class Order:
    def __init__(self, token_get: Address, amount_get: Wad, token_give: Address, amount_give: Wad, expires: int):
        self.token_get = token_get
        self.amount_get = amount_get
        self.token_give = token_give
        self.amount_give = amount_give
        self.expires = expires
        self.nonce = None
        self.user = None
        self.v = None
        self.r = None
        self.s = None


class OffChainOrder(Order):
    def __init__(self, token_get: Address, amount_get: Wad, token_give: Address, amount_give: Wad, expires: int,
                 nonce: int, user: Address, v: int, r: bytes, s: bytes):
        super().__init__(token_get, amount_get, token_give, amount_give, expires)
        self.nonce = nonce
        self.user = user
        self.v = v
        self.r = r
        self.s = s


class OnChainOrder(Order):
    def __init__(self, token_get: Address, amount_get: Wad, token_give: Address, amount_give: Wad, expires: int,
                 nonce: int, user: Address):
        super().__init__(token_get, amount_get, token_give, amount_give, expires)
        self.nonce = nonce
        self.user = user


class EtherDelta(Contract):
    """A client for the EtherDelta exchange contract.

    You can find the source code of the `EtherDelta` contract here:
    <https://etherscan.io/address/0x8d12a197cb00d4747a1fe03395095ce2a5cc6819#code>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `EtherDelta` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/EtherDelta.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def approve(self, tokens: List[ERC20Token], approval_function):
        for token in tokens:
            approval_function(token, self.address, 'EtherDelta')

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

    def fee_make(self) -> Wad:
        return Wad(self._contract.call().feeMake())

    def fee_take(self) -> Wad:
        return Wad(self._contract.call().feeTake())

    def fee_rebate(self) -> Wad:
        return Wad(self._contract.call().feeRebate())

    def deposit(self, amount: Wad) -> Optional[Receipt]:
        """Deposits `amount` of raw ETH to EtherDelta.

        Args:
            amount: Amount of raw ETH to be deposited on EtherDelta.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the amount has been deposited.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"EtherDelta('{self.address}').deposit() with value='{amount}'",
                              lambda: self._contract.transact({'value': amount.value}).deposit())

    def withdraw(self, amount: Wad) -> Optional[Receipt]:
        """Withdraws `amount` of raw ETH from EtherDelta.

        The withdrawn ETH will get transferred to the calling account.

        Args:
            amount: Amount of raw ETH to be withdrawn from EtherDelta.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the amount has been withdrawn.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"EtherDelta('{self.address}').withdraw('{amount}')",
                              lambda: self._contract.transact().withdraw(amount.value))

    def balance_of(self, user: Address) -> Wad:
        """Returns the amount of raw ETH deposited by the specified user.

        Args:
            user: Address of the user to check the balance of.

        Returns:
            The raw ETH balance kept in the EtherDelta contract by the specified user.
        """
        assert(isinstance(user, Address))
        return Wad(self._contract.call().balanceOf('0x0000000000000000000000000000000000000000', user.address))

    def deposit_token(self, token: Address, amount: Wad) -> Optional[Receipt]:
        """Deposits `amount` of token `token` to EtherDelta.

        Tokens will be pulled from the calling account, so the EtherDelta contract needs
        to have appropriate allowance. Either call `approve()` or set the allowance manually
        before trying to deposit tokens.

        Args:
            token: Address of the token to be deposited.
            amount: Amount of token `token` to be deposited on EtherDelta.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the tokens have been deposited.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(token, Address))
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"EtherDelta('{self.address}').depositToken('{token}', '{amount}')",
                              lambda: self._contract.transact().depositToken(token.address, amount.value))

    def withdraw_token(self, token: Address, amount: Wad) -> Optional[Receipt]:
        """Withdraws `amount` of token `token` from EtherDelta.

        Tokens will get transferred to the calling account.

        Args:
            token: Address of the token to be withdrawn.
            amount: Amount of token `token` to be withdrawn from EtherDelta.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the tokens have been withdrawn.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(token, Address))
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"EtherDelta('{self.address}').withdrawToken('{token}', '{amount}')",
                              lambda: self._contract.transact().withdrawToken(token.address, amount.value))

    def balance_of_token(self, token: Address, user: Address) -> Wad:
        """Returns the amount of token `token` deposited by the specified user.

        Args:
            token: Address of the token return the balance of.
            user: Address of the user to check the balance of.

        Returns:
            The token `token` balance kept in the EtherDelta contract by the specified user.
        """
        assert(isinstance(token, Address))
        assert(isinstance(user, Address))
        return Wad(self._contract.call().balanceOf(token.address, user.address))

    #TODO remove nonce...?
    def place_order_onchain(self,
                            token_get: Address,
                            amount_get: Wad,
                            token_give: Address,
                            amount_give: Wad,
                            expires: int,
                            nonce: int) -> Optional[Receipt]:

        return self._transact(self.web3, f"EtherDelta('{self.address}').order('{token_get}', '{amount_get}',"
                                         f" '{token_give}', '{amount_give}', '{expires}', '{nonce}')",
                              lambda: self._contract.transact().order(token_get.address, amount_get.value,
                                                                      token_give.address, amount_give.value,
                                                                      expires, nonce))

    def place_order_offchain(self,
                             token_get: Address,
                             amount_get: Wad,
                             token_give: Address,
                             amount_give: Wad,
                             expires: int) -> OffChainOrder:

        def encode_address(address: Address) -> bytes:
            return get_single_encoder("address", None, None)(address.address)[12:]

        def encode_uint256(value: int) -> bytes:
            return get_single_encoder("uint", 256, None)(value)

        nonce = random.randint(0, 2**256 - 1)
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
                                                         self._none_as_zero(order.v),
                                                         self._none_as_empty(order.r),
                                                         self._none_as_empty(order.s)))

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
                                                      self._none_as_zero(order.v),
                                                      self._none_as_empty(order.r),
                                                      self._none_as_empty(order.s)))

    def trade(self, order: Order, amount: Wad) -> Optional[Receipt]:
        """Takes (buys) an order.

        `amount` is in `token_get` terms, it is the amount you want to buy with. It can not be higher
        than `available_volume(order)`.

        The 'amount' of `token_get` tokens will get deducted from your EtherDelta balance if the trade was
        successful. The corresponding amount of `token_have` tokens will be added to your EtherDelta balance.

        Args:
            order: The order you want to take (buy). Can be either an `OnChainOrder` or an `OffChainOrder`.
            amount: Amount of `token_get` tokens that you want to be deducted from your EtherDelta balance
                in order to buy a corresponding amount of `token_have` tokens.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and so was the trade.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(order, Order))
        assert(isinstance(amount, Wad))

        return self._transact(self.web3, f"EtherDelta('{self.address}').trade('{order.token_get}',"
                                         f" '{order.amount_get}', '{order.token_give}', '{order.amount_give}',"
                                         f" '{order.expires}', '{order.nonce}', '{order.user}', '0x...', '0x...',"
                                         f" '0x...', '{amount}')",
                              lambda: self._contract.transact().trade(order.token_get.address,
                                                                      order.amount_get.value,
                                                                      order.token_give.address,
                                                                      order.amount_give.value,
                                                                      order.expires,
                                                                      order.nonce,
                                                                      order.user.address,
                                                                      self._none_as_zero(order.v),
                                                                      self._none_as_empty(order.r),
                                                                      self._none_as_empty(order.s),
                                                                      amount.value))

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
                                               self._none_as_zero(order.v),
                                               self._none_as_empty(order.r),
                                               self._none_as_empty(order.s),
                                               amount.value,
                                               self.web3.eth.defaultAccount)

    def cancel_order(self, order: Order) -> Optional[Receipt]:
        """Cancels an existing order.

        Orders can be cancelled only by their owners.

        Args:
            order: The order you want to cancel. Can be either an `OnChainOrder` or an `OffChainOrder`.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the order has been cancelled.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(order, Order))

        return self._transact(self.web3, f"EtherDelta('{self.address}').cancelOrder('{order.token_get}',"
                                         f" '{order.amount_get}', '{order.token_give}', '{order.amount_give}',"
                                         f" '{order.expires}', '{order.nonce}', '0x...', '0x...', '0x...')",
                              lambda: self._contract.transact().cancelOrder(order.token_get.address,
                                                                            order.amount_get.value,
                                                                            order.token_give.address,
                                                                            order.amount_give.value,
                                                                            order.expires,
                                                                            order.nonce,
                                                                            self._none_as_zero(order.v),
                                                                            self._none_as_empty(order.r),
                                                                            self._none_as_empty(order.s)))

    @coerce_return_to_text
    def _eth_sign(self, account, data_hash):
        return self.web3._requestManager.request_blocking(
            "eth_sign", [account, encode_hex(data_hash)],
        )

    @staticmethod
    def _none_as_zero(x: int) -> int:
        return x if x else 0

    @staticmethod
    def _none_as_empty(x: bytes) -> bytes:
        return x if x else bytes()
