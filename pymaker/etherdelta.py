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

import hashlib
import json
import logging
import random
import threading
from pprint import pformat
from subprocess import Popen, PIPE
from typing import List

from web3 import Web3

from pymaker import Contract, Address, Transact
from pymaker.numeric import Wad
from pymaker.sign import eth_sign, to_vrs
from pymaker.tightly_packed import encode_address, encode_uint256
from pymaker.token import ERC20Token
from pymaker.util import bytes_to_hexstring, hexstring_to_bytes


class Order:
    """An off-chain order placed on the EtherDelta exchange.

    Attributes:
        maker: Order creator.
        pay_token: Address of the ERC20 token put on sale.
        pay_amount: Amount of the `pay_token` token put on sale.
        buy_token: Address of the ERC20 token to be bought.
        buy_amount: Amount of the `buy_token` to be bought.
        expires: The block number after which the order will expire.
        nonce: Nonce number, used to make orders similar unique and randomize signatures.
        v: V component of the order signature.
        r: R component of the order signature.
        s: S component of the order signature.
    """
    def __init__(self, ether_delta, maker: Address, pay_token: Address, pay_amount: Wad, buy_token: Address,
                 buy_amount: Wad, expires: int, nonce: int, v: int, r: bytes, s: bytes):

        assert(isinstance(maker, Address))
        assert(isinstance(pay_token, Address))
        assert(isinstance(pay_amount, Wad))
        assert(isinstance(buy_token, Address))
        assert(isinstance(buy_amount, Wad))
        assert(isinstance(expires, int))
        assert(isinstance(nonce, int))
        assert(isinstance(v, int))
        assert(isinstance(r, bytes))
        assert(isinstance(s, bytes))

        self._ether_delta = ether_delta
        self.maker = maker
        self.pay_token = pay_token
        self.pay_amount = pay_amount
        self.buy_token = buy_token
        self.buy_amount = buy_amount
        self.expires = expires
        self.nonce = nonce
        self.v = v
        self.r = r
        self.s = s

    @property
    def sell_to_buy_price(self) -> Wad:
        return self.pay_amount / self.buy_amount

    @property
    def buy_to_sell_price(self) -> Wad:
        return self.buy_amount / self.pay_amount

    @property
    def remaining_buy_amount(self) -> Wad:
        return self.buy_amount - self._ether_delta.amount_filled(self)

    @property
    def remaining_sell_amount(self) -> Wad:
        return self.pay_amount - (self._ether_delta.amount_filled(self) * self.pay_amount / self.buy_amount)

    @staticmethod
    def from_json(ether_delta, data: dict):
        assert(isinstance(data, dict))
        return Order(ether_delta=ether_delta, maker=Address(data['user']), pay_token=Address(data['tokenGive']),
                     pay_amount=Wad(int(data['amountGive'])), buy_token=Address(data['tokenGet']),
                     buy_amount=Wad(int(data['amountGet'])), expires=int(data['expires']), nonce=int(data['nonce']),
                     v=int(data['v']), r=hexstring_to_bytes(data['r']), s=hexstring_to_bytes(data['s']))

    def to_json(self) -> dict:
        return {'contractAddr': self._ether_delta.address.address,
                'tokenGet': self.buy_token.address,
                'amountGet': self.buy_amount.value,
                'tokenGive': self.pay_token.address,
                'amountGive': self.pay_amount.value,
                'expires': self.expires,
                'nonce': self.nonce,
                'v': self.v,
                'r': bytes_to_hexstring(self.r),
                's': bytes_to_hexstring(self.s),
                'user': self.maker.address}

    def __eq__(self, other):
        assert(isinstance(other, Order))
        return self.maker == other.maker and \
               self.pay_token == other.pay_token and \
               self.pay_amount == other.pay_amount and \
               self.buy_token == other.buy_token and \
               self.buy_amount == other.buy_amount and \
               self.expires == other.expires and \
               self.nonce == other.nonce and \
               self.v == other.v and \
               self.r == other.r and \
               self.s == other.s

    def __hash__(self):
        return hash((self.maker,
                     self.pay_token,
                     self.pay_amount,
                     self.buy_token,
                     self.buy_amount,
                     self.expires,
                     self.nonce,
                     self.v,
                     self.r,
                     self.s))

    def __str__(self):
        return f"('{self.buy_token}', '{self.buy_amount}'," \
               f" '{self.pay_token}', '{self.pay_amount}'," \
               f" '{self.expires}', '{self.nonce}')"

    def __repr__(self):
        return pformat(vars(self))


class LogTrade:
    def __init__(self, log):
        self.maker = Address(log['args']['get'])
        self.taker = Address(log['args']['give'])
        self.pay_token = Address(log['args']['tokenGive'])
        self.take_amount = Wad(log['args']['amountGive'])
        self.buy_token = Address(log['args']['tokenGet'])
        self.give_amount = Wad(log['args']['amountGet'])
        self.raw = log

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
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def approve(self, tokens: List[ERC20Token], approval_function):
        """Approve the EtherDelta contract to fully access balances of specified tokens.

        For available approval functions (i.e. approval modes) see `directly` and `via_tx_manager`
        in `pymaker.approval`.

        Args:
            tokens: List of :py:class:`pymaker.token.ERC20Token` class instances.
            approval_function: Approval function (i.e. approval mode).
        """
        assert(isinstance(tokens, list))
        assert(callable(approval_function))

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

    def account_levels_addr(self) -> Address:
        """Returns the address of the AccountLevels contract.

        Returns:
            The address of the AccountLevels contract.
        """
        return Address(self._contract.call().accountLevelsAddr())

    def fee_make(self) -> Wad:
        """Returns the maker fee configured in the contract.

        Returns:
            The maker fee.
        """
        return Wad(self._contract.call().feeMake())

    def fee_take(self) -> Wad:
        """Returns the taker fee configured in the contract.

        Returns:
            The taker fee.
        """
        return Wad(self._contract.call().feeTake())

    def fee_rebate(self) -> Wad:
        """Returns the rebate fee configured in the contract.

        Plase see the contract source code for more details.

        Returns:
            The rebate fee.
        """
        return Wad(self._contract.call().feeRebate())

    def past_trade(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogTrade]:
        """Synchronously retrieve past LogTrade events.

        `LogTrade` events are emitted by the EtherDelta contract every time someone takes an order.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `LogTrade` events represented as :py:class:`pymaker.etherdelta.LogTrade` class.
        """
        assert(isinstance(number_of_past_blocks, int))
        assert(isinstance(event_filter, dict) or (event_filter is None))

        return self._past_events(self._contract, 'Trade', LogTrade, number_of_past_blocks, event_filter)

    def deposit(self, amount: Wad) -> Transact:
        """Deposits `amount` of raw ETH to EtherDelta.

        Args:
            amount: Amount of raw ETH to be deposited on EtherDelta.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(amount, Wad))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'deposit', [], {'value': amount.value})

    def withdraw(self, amount: Wad) -> Transact:
        """Withdraws `amount` of raw ETH from EtherDelta.

        The withdrawn ETH will get transferred to the calling account.

        Args:
            amount: Amount of raw ETH to be withdrawn from EtherDelta.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
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
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
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
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
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

    def create_order(self,
                     pay_token: Address,
                     pay_amount: Wad,
                     buy_token: Address,
                     buy_amount: Wad,
                     expires: int) -> Order:
        """Creates a new off-chain order.

        Although it's not necessary to have any amount of `pay_token` deposited to EtherDelta
        before placing an order, nobody will be able to take this order until some balance of
        'pay_token' is provided.

        If you want to trade raw ETH, pass `Address('0x0000000000000000000000000000000000000000')`
        as either `pay_token` or `buy_token`.

        Args:
            pay_token: Address of the ERC20 token you want to put on sale.
            pay_amount: Amount of the `pay_token` token you want to put on sale.
            buy_token: Address of the ERC20 token you want to be paid with.
            buy_amount:  Amount of the `buy_token` you want to receive.
            expires: The block number after which the order will expire.

        Returns:
            Newly created order as an instance of the :py:class:`pymaker.etherdelta.Order` class.
        """

        assert(isinstance(pay_token, Address))
        assert(isinstance(pay_amount, Wad))
        assert(isinstance(buy_token, Address))
        assert(isinstance(buy_amount, Wad))
        assert(isinstance(expires, int) and (expires > 0))
        assert(pay_amount > Wad(0))
        assert(buy_amount > Wad(0))

        nonce = self.random_nonce()
        order_hash = hashlib.sha256(encode_address(self.address) +
                                    encode_address(buy_token) +
                                    encode_uint256(buy_amount.value) +
                                    encode_address(pay_token) +
                                    encode_uint256(pay_amount.value) +
                                    encode_uint256(expires) +
                                    encode_uint256(nonce)).digest()

        signature = eth_sign(order_hash, self.web3)
        v, r, s = to_vrs(signature)

        return Order(self, Address(self.web3.eth.defaultAccount), pay_token, pay_amount, buy_token, buy_amount,
                     expires, nonce, v, r, s)

    def amount_available(self, order: Order) -> Wad:
        """Returns the amount that is still available (tradeable) for an order.

        The result will never be greater than `order.buy_amount - amount_filled(order)`.
        It can be lower though if the order maker does not have enough balance on EtherDelta.

        Args:
            order: The order object you want to know the available amount of.

        Returns:
            The available amount for the order, in terms of `buy_token`.
        """
        assert(isinstance(order, Order))

        return Wad(self._contract.call().availableVolume(order.buy_token.address,
                                                         order.buy_amount.value,
                                                         order.pay_token.address,
                                                         order.pay_amount.value,
                                                         order.expires,
                                                         order.nonce,
                                                         order.maker.address,
                                                         order.v if hasattr(order, 'v') else 0,
                                                         order.r if hasattr(order, 'r') else bytes(),
                                                         order.s if hasattr(order, 's') else bytes()))

    def amount_filled(self, order: Order) -> Wad:
        """Returns the amount that has been already filled for an order.

        The result will never be greater than `order.buy_amount`. It can be lower though
        if the order maker does not have enough balance on EtherDelta.

        If an order has been cancelled, `amount_filled(order)` will be always equal
        to `order.buy_amount`. Cancelled orders basically look like completely filled ones.

        Args:
            order: The order object you want to know the filled amount of.

        Returns:
            The amount already filled for the order, in terms of `buy_token`.
        """
        assert(isinstance(order, Order))

        return Wad(self._contract.call().amountFilled(order.buy_token.address,
                                                      order.buy_amount.value,
                                                      order.pay_token.address,
                                                      order.pay_amount.value,
                                                      order.expires,
                                                      order.nonce,
                                                      order.maker.address,
                                                      order.v if hasattr(order, 'v') else 0,
                                                      order.r if hasattr(order, 'r') else bytes(),
                                                      order.s if hasattr(order, 's') else bytes()))

    def trade(self, order: Order, amount: Wad) -> Transact:
        """Takes (buys) an order.

        `amount` is in `buy_token` terms, it is the amount you want to buy with. It can not be higher
        than `amount_available(order)`.

        The 'amount' of `buy_token` tokens will get deducted from your EtherDelta balance if the trade was
        successful. The corresponding amount of `pay_token` tokens will be added to your EtherDelta balance.

        Args:
            order: The order you want to take (buy).
            amount: Amount of `buy_token` tokens that you want to be deducted from your EtherDelta balance
                in order to buy a corresponding amount of `pay_token` tokens.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(order, Order))
        assert(isinstance(amount, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'trade',
                        [order.buy_token.address,
                         order.buy_amount.value,
                         order.pay_token.address,
                         order.pay_amount.value,
                         order.expires,
                         order.nonce,
                         order.maker.address,
                         order.v if hasattr(order, 'v') else 0,
                         order.r if hasattr(order, 'r') else bytes(),
                         order.s if hasattr(order, 's') else bytes(),
                         amount.value])

    def can_trade(self, order: Order, amount: Wad) -> bool:
        """Verifies whether a trade can be executed.

        Verifies whether amount `amount` can be traded on order `order` i.e. whether the `trade()`
        method executed with exactly the same parameters should succeed.

        Args:
            order: The order you want to verify the trade for.
            amount: Amount expressed in terms of `buy_token` that you want to verify the trade for.

        Returns:
            'True' if the given amount can be traded on this order. `False` otherwise.
        """
        assert(isinstance(order, Order))
        assert(isinstance(amount, Wad))

        return self._contract.call().testTrade(order.buy_token.address,
                                               order.buy_amount.value,
                                               order.pay_token.address,
                                               order.pay_amount.value,
                                               order.expires,
                                               order.nonce,
                                               order.maker.address,
                                               order.v if hasattr(order, 'v') else 0,
                                               order.r if hasattr(order, 'r') else bytes(),
                                               order.s if hasattr(order, 's') else bytes(),
                                               amount.value,
                                               self.web3.eth.defaultAccount)

    def cancel_order(self, order: Order) -> Transact:
        """Cancels an existing order.

        Orders can be cancelled only by their owners.

        Args:
            order: The order you want to cancel.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(order, Order))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'cancelOrder',
                        [order.buy_token.address,
                         order.buy_amount.value,
                         order.pay_token.address,
                         order.pay_amount.value,
                         order.expires,
                         order.nonce,
                         order.v if hasattr(order, 'v') else 0,
                         order.r if hasattr(order, 'r') else bytes(),
                         order.s if hasattr(order, 's') else bytes()])

    @staticmethod
    def random_nonce():
        return random.randint(1, 2**32 - 1)

    def __repr__(self):
        return f"EtherDelta('{self.address}')"


class EtherDeltaApi:
    """A client for the EtherDelta API backend.

    Attributes:
        client_tool_directory: Directory containing the `etherdelta-client` tool.
        client_tool_command: Command for running the `etherdelta-client` tool.
        api_server: Base URL of the EtherDelta API backend server.
        number_of_attempts: Number of attempts to run the `etherdelta-client` tool.
        retry_interval: Interval between subsequent retries if order placement failed,
            within one `etherdelta-client` run.
        timeout: Timeout after which publish order is considered as failed by the
            `etherdelta-client` tool. If number_of_attempts > 1, this tool will be
            run several times though.
    """
    logger = logging.getLogger()

    def __init__(self,
                 client_tool_directory: str,
                 client_tool_command: str,
                 api_server: str,
                 number_of_attempts: int,
                 retry_interval: int,
                 timeout: int):
        assert(isinstance(client_tool_directory, str))
        assert(isinstance(client_tool_command, str))
        assert(isinstance(api_server, str))
        assert(isinstance(number_of_attempts, int))
        assert(isinstance(retry_interval, int))
        assert(isinstance(timeout, int))

        self.client_tool_directory = client_tool_directory
        self.client_tool_command = client_tool_command
        self.api_server = api_server
        self.number_of_attempts = number_of_attempts
        self.retry_interval = retry_interval
        self.timeout = timeout

    def publish_order(self, order: Order):
        assert(isinstance(order, Order))

        def _publish_order_via_client() -> bool:
            process = Popen(self.client_tool_command.split() + ['--url', self.api_server,
                                                                '--timeout', str(self.timeout),
                                                                '--retry-interval', str(self.retry_interval),
                                                                json.dumps(order.to_json())],
                            cwd=self.client_tool_directory, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)

            result = process.communicate(None, timeout=self.timeout+15)
            stdout = result[0].decode("utf-8").rstrip().replace('\n', ' -> ')
            stderr = result[1].decode("utf-8").rstrip().replace('\n', ' -> ')

            if len(stdout) > 0:
                if process.returncode == 0:
                    self.logger.info(f"Output from 'etherdelta-client': {stdout}")
                else:
                    self.logger.warning(f"Non-zero exit code output from 'etherdelta-client': {stdout}")

            if len(stderr) > 0:
                self.logger.fatal(f"Error from 'etherdelta-client': {stderr}")

            return process.returncode == 0

        def _run():
            for attempt in range(self.number_of_attempts):
                self.logger.info(f"Sending order (attempt #{attempt+1}): {order}")
                if _publish_order_via_client():
                    self.logger.info(f"Order {order} sent successfully")
                    return

            self.logger.warning(f"Failed to send order {order}")

        threading.Thread(target=_run, daemon=True).start()

    def __repr__(self):
        return f"EtherDeltaApi()"
