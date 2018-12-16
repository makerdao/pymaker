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

from pprint import pformat
from typing import Optional, List, Iterable, Iterator

from hexbytes import HexBytes
from web3 import Web3
from web3.utils.events import get_event_data

from pymaker import Contract, Address, Transact, Receipt
from pymaker.numeric import Wad
from pymaker.token import ERC20Token
from pymaker.util import int_to_bytes32, bytes_to_int


class Order:
    """Represents a single order on `OasisDEX`.

    Instances of this class shouldn't be created directly. Instead of that, new orders can be queried
    using methods of :py:class:`pymaker.oasis.SimpleMarket`, :py:class:`pymaker.oasis.ExpiringMarket`
    or :py:class:`pymaker.oasis.MatchingMarket`.

    Attributes:
        order_id: Id of the order.
        maker: Ethereum address of the owner of this order.
        pay_token: The address of the token which is put on sale.
        pay_amount: The amount of the `pay_token` token which is put on sale.
        buy_token: The address of the token the order creator wants to be paid with.
        buy_amount: The price the order creator wants to be paid, denominated in the `buy_token` token.
        timestamp: Date and time when this order has been created, as a unix timestamp.
    """

    def __init__(self, market, order_id: int, maker: Address, pay_token: Address, pay_amount: Wad, buy_token: Address,
                 buy_amount: Wad, timestamp: int):
        assert(isinstance(order_id, int))
        assert(isinstance(maker, Address))
        assert(isinstance(pay_token, Address))
        assert(isinstance(pay_amount, Wad))
        assert(isinstance(buy_token, Address))
        assert(isinstance(buy_amount, Wad))
        assert(isinstance(timestamp, int))

        self._market = market
        self.order_id = order_id
        self.maker = maker
        self.pay_token = pay_token
        self.pay_amount = pay_amount
        self.buy_token = buy_token
        self.buy_amount = buy_amount
        self.timestamp = timestamp

    @property
    def sell_to_buy_price(self) -> Wad:
        return self.pay_amount / self.buy_amount

    @property
    def buy_to_sell_price(self) -> Wad:
        return self.buy_amount / self.pay_amount

    @property
    def remaining_buy_amount(self) -> Wad:
        return self.buy_amount

    @property
    def remaining_sell_amount(self) -> Wad:
        return self.pay_amount

    def __eq__(self, other):
        assert(isinstance(other, Order))
        return self._market.address == other._market.address and self.order_id == other.order_id

    def __hash__(self):
        return self.order_id

    def __repr__(self):
        return pformat(vars(self))


class LogMake:
    def __init__(self, log):
        self.order_id = bytes_to_int(log['args']['id'])
        self.maker = Address(log['args']['maker'])
        self.pay_token = Address(log['args']['pay_gem'])
        self.pay_amount = Wad(log['args']['pay_amt'])
        self.buy_token = Address(log['args']['buy_gem'])
        self.buy_amount = Wad(log['args']['buy_amt'])
        self.timestamp = log['args']['timestamp']
        self.raw = log

    @classmethod
    def from_receipt(cls, receipt: Receipt):
        assert(isinstance(receipt, Receipt))

        if receipt.logs is not None:
            for log in receipt.logs:
                if len(log['topics']) > 0 and log['topics'][0] == HexBytes('0x773ff502687307abfa024ac9f62f9752a0d210dac2ffd9a29e38e12e2ea82c82'):
                    log_make_abi = [abi for abi in SimpleMarket.abi if abi.get('name') == 'LogMake'][0]
                    event_data = get_event_data(log_make_abi, log)

                    yield LogMake(event_data)

    def __repr__(self):
        return pformat(vars(self))


class LogBump:
    def __init__(self, log):
        self.order_id = bytes_to_int(log['args']['id'])
        self.maker = Address(log['args']['maker'])
        self.pay_token = Address(log['args']['pay_gem'])
        self.pay_amount = Wad(log['args']['pay_amt'])
        self.buy_token = Address(log['args']['buy_gem'])
        self.buy_amount = Wad(log['args']['buy_amt'])
        self.timestamp = log['args']['timestamp']
        self.raw = log

    def __repr__(self):
        return pformat(vars(self))


class LogTake:
    def __init__(self, log):
        self.order_id = bytes_to_int(log['args']['id'])
        self.maker = Address(log['args']['maker'])
        self.taker = Address(log['args']['taker'])
        self.pay_token = Address(log['args']['pay_gem'])
        self.take_amount = Wad(log['args']['take_amt'])
        self.buy_token = Address(log['args']['buy_gem'])
        self.give_amount = Wad(log['args']['give_amt'])
        self.timestamp = log['args']['timestamp']
        self.raw = log

    @classmethod
    def from_event(cls, event: dict):
        assert(isinstance(event, dict))

        topics = event.get('topics')
        if topics and topics[0] == HexBytes('0x3383e3357c77fd2e3a4b30deea81179bc70a795d053d14d5b7f2f01d0fd4596f'):
            log_take_abi = [abi for abi in SimpleMarket.abi if abi.get('name') == 'LogTake'][0]
            event_data = get_event_data(log_take_abi, event)

            return LogTake(event_data)

    def __eq__(self, other):
        assert(isinstance(other, LogTake))
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return pformat(vars(self))


class LogKill:
    def __init__(self, log):
        self.order_id = bytes_to_int(log['args']['id'])
        self.maker = Address(log['args']['maker'])
        self.pay_token = Address(log['args']['pay_gem'])
        self.pay_amount = Wad(log['args']['pay_amt'])
        self.buy_token = Address(log['args']['buy_gem'])
        self.buy_amount = Wad(log['args']['buy_amt'])
        self.timestamp = log['args']['timestamp']
        self.raw = log

    def __repr__(self):
        return pformat(vars(self))


class SimpleMarket(Contract):
    """A client for a `SimpleMarket` contract.

    `SimpleMarket` is a simple on-chain OTC market for ERC20-compatible tokens.
    It powers the `OasisDEX` decentralized exchange.

    You can find the source code of the `OasisDEX` contracts here:
    <https://github.com/makerdao/maker-otc>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `SimpleMarket` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/SimpleMarket.abi')
    bin = Contract._load_bin(__name__, 'abi/SimpleMarket.bin')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3):
        """Deploy a new instance of the `SimpleMarket` contract.

        Args:
            web3: An instance of `Web3` from `web3.py`.

        Returns:
            A `SimpleMarket` class instance.
        """
        return SimpleMarket(web3=web3, address=Contract._deploy(web3, SimpleMarket.abi, SimpleMarket.bin, []))

    def approve(self, tokens: List[ERC20Token], approval_function):
        """Approve the OasisDEX contract to fully access balances of specified tokens.

        For available approval functions (i.e. approval modes) see `directly` and `via_tx_manager`
        in `pymaker.approval`.

        Args:
            tokens: List of :py:class:`pymaker.token.ERC20Token` class instances.
            approval_function: Approval function (i.e. approval mode).
        """
        assert(isinstance(tokens, list))
        assert(callable(approval_function))

        for token in tokens:
            approval_function(token, self.address, 'OasisDEX')

    def past_make(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogMake]:
        """Synchronously retrieve past LogMake events.

        `LogMake` events are emitted by the Oasis contract every time someone places an order.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `LogMake` events represented as :py:class:`pymaker.oasis.LogMake` class.
        """
        assert(isinstance(number_of_past_blocks, int))
        assert(isinstance(event_filter, dict) or (event_filter is None))

        return self._past_events(self._contract, 'LogMake', LogMake, number_of_past_blocks, event_filter)

    def past_bump(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogBump]:
        """Synchronously retrieve past LogBump events.

        `LogBump` events are emitted by the Oasis contract every time someone calls the `bump()` function.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `LogBump` events represented as :py:class:`pymaker.oasis.LogBump` class.
        """
        assert(isinstance(number_of_past_blocks, int))
        assert(isinstance(event_filter, dict) or (event_filter is None))

        return self._past_events(self._contract, 'LogBump', LogBump, number_of_past_blocks, event_filter)

    def past_take(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogTake]:
        """Synchronously retrieve past LogTake events.

        `LogTake` events are emitted by the Oasis contract every time someone takes an order.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `LogTake` events represented as :py:class:`pymaker.oasis.LogTake` class.
        """
        assert(isinstance(number_of_past_blocks, int))
        assert(isinstance(event_filter, dict) or (event_filter is None))

        return self._past_events(self._contract, 'LogTake', LogTake, number_of_past_blocks, event_filter)

    def past_kill(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogKill]:
        """Synchronously retrieve past LogKill events.

        `LogKill` events are emitted by the Oasis contract every time someone cancels an order.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `LogKill` events represented as :py:class:`pymaker.oasis.LogKill` class.
        """
        assert(isinstance(number_of_past_blocks, int))
        assert(isinstance(event_filter, dict) or (event_filter is None))

        return self._past_events(self._contract, 'LogKill', LogKill, number_of_past_blocks, event_filter)

    def get_last_order_id(self) -> int:
        """Get the id of the last order created on the market.

        Returns:
            The id of the last order. Returns `0` if no orders have been created at all.
        """
        return self._contract.call().last_offer_id()

    def get_order(self, order_id: int) -> Optional[Order]:
        """Get order details.

        Args:
            order_id: The id of the order to get the details of.

        Returns:
            An instance of `Order` if the order is still active, or `None` if the order has been
            either already completely taken or cancelled.
        """
        assert(isinstance(order_id, int))

        array = self._contract.call().offers(order_id)
        if array[5] == 0:
            return None
        else:
            return Order(market=self, order_id=order_id, maker=Address(array[4]), pay_token=Address(array[1]),
                         pay_amount=Wad(array[0]), buy_token=Address(array[3]), buy_amount=Wad(array[2]),
                         timestamp=array[5])

    def get_orders(self, pay_token: Address = None, buy_token: Address = None) -> List[Order]:
        """Get all active orders.

        If both `pay_token` and `buy_token` are specified, orders will be filtered by these.
        Either none or both of these parameters have to be specified.

        Args:
            `pay_token`: Address of the `pay_token` to filter the orders by.
            `buy_token`: Address of the `buy_token` to filter the orders by.

        Returns:
            A list of `Order` objects representing all active orders on Oasis.
        """
        assert((isinstance(pay_token, Address) and isinstance(buy_token, Address))
               or (pay_token is None and buy_token is None))

        orders = [self.get_order(order_id + 1) for order_id in range(self.get_last_order_id())]
        orders = [order for order in orders if order is not None]

        if pay_token is not None and buy_token is not None:
            orders = list(filter(lambda order: order.pay_token == pay_token and order.buy_token == buy_token, orders))

        return orders

    def get_orders_by_maker(self, maker: Address) -> List[Order]:
        """Get all active orders created by `maker`.

        Args:
            maker: Address of the `maker` to filter the orders by.

        Returns:
            A list of `Order` objects representing all active orders belonging to this `maker`.
        """
        assert(isinstance(maker, Address))

        result = []
        for order_id in range(self.get_last_order_id()):
            # Query the order.
            order = self.get_order(order_id + 1)
            if order is None:
                continue

            # We are only interested in orders owned by `maker`. In case the order is not owned by `maker`,
            # we add it to `_alien_orders[maker]` so the next time `get_orders_by_maker()` is called
            # with the same parameter we will be able to rule out these orders straight away.
            if order.maker != maker:
                continue

            result.append(order)

        return result

    def make(self, pay_token: Address, pay_amount: Wad, buy_token: Address, buy_amount: Wad) -> Transact:
        """Create a new order.

        The `pay_amount` of `pay_token` token will be taken from you on order creation and deposited
        in the market contract. Allowance needs to be set first - refer to the `approve()` method.

        When complete, `receipt.result` will contain order_id of the new order.

        Args:
            pay_token: Address of the ERC20 token you want to put on sale.
            pay_amount: Amount of the `pay_token` token you want to put on sale.
            buy_token: Address of the ERC20 token you want to be paid with.
            buy_amount: Amount of the `buy_token` you want to receive.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(pay_token, Address))
        assert(isinstance(pay_amount, Wad))
        assert(isinstance(buy_token, Address))
        assert(isinstance(buy_amount, Wad))
        assert(pay_amount > Wad(0))
        assert(buy_amount > Wad(0))

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'make', [pay_token.address, buy_token.address, pay_amount.value, buy_amount.value], None,
                        self._make_order_id_result_function)

    def bump(self, order_id: int) -> Transact:
        """Bumps an order.

        Bumping an order generates a `LogBump` event, which can make the order reappear
        in some front-ends relying on the events.

        Args:
            order_id: Id of the order you want to bump.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(order_id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'bump',
                        [int_to_bytes32(order_id)])

    def take(self, order_id: int, quantity: Wad) -> Transact:
        """Takes (buys) an order.

        If `quantity` is equal to `pay_amount`, the whole order will be taken (bought) which will make it
        disappear from the order book. If you want to buy a fraction of the order, set `quantity` to a number
        lower than `pay_amount`.

        Args:
            order_id: Id of the order you want to take (buy).
            quantity: Quantity of `pay_token` that you want to buy.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(order_id, int))
        assert(isinstance(quantity, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'take',
                        [int_to_bytes32(order_id), quantity.value])

    def kill(self, order_id: int) -> Transact:
        """Cancels an existing order.

        Orders can be cancelled only by their owners. In addition to that, in case of expiring markets,
        after the market has expired all orders can be cancelled by anyone.

        Args:
            order_id: Id of the order you want to cancel.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(order_id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kill(bytes32)', [int_to_bytes32(order_id)])

    @staticmethod
    def _make_order_id_result_function(receipt):
        return next(map(lambda log_make: log_make.order_id, LogMake.from_receipt(receipt)), None)

    def __repr__(self):
        return f"SimpleMarket('{self.address}')"


class ExpiringMarket(SimpleMarket):
    """A client for a `ExpiringMarket` contract.

    You can find the source code of the `OasisDEX` contracts here:
    <https://github.com/makerdao/maker-otc>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `ExpiringMarket` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/ExpiringMarket.abi')
    bin = Contract._load_bin(__name__, 'abi/ExpiringMarket.bin')

    @staticmethod
    def deploy(web3: Web3, close_time: int):
        """Deploy a new instance of the `ExpiringMarket` contract.

        Args:
            web3: An instance of `Web` from `web3.py`.
            close_time: Unix timestamp of when the market will close.

        Returns:
            A `ExpiringMarket` class instance.
        """
        return ExpiringMarket(web3=web3, address=Contract._deploy(web3, ExpiringMarket.abi, ExpiringMarket.bin,
                                                                  [close_time]))

    def is_closed(self) -> bool:
        """Check if the market is closed.

        Returns:
            `True` if the market is closed. `False` otherwise.
        """
        return self._contract.call().isClosed()

    def __repr__(self):
        return f"ExpiringMarket('{self.address}')"


class MatchingMarket(ExpiringMarket):
    """A client for a `MatchingMarket` contract.

    You can find the source code of the `OasisDEX` contracts here:
    <https://github.com/makerdao/maker-otc>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `MatchingMarket` contract.
        support_address: Ethereum address of the `MakerOtcSupportMethods` contract (optional).
    """

    abi = Contract._load_abi(__name__, 'abi/MatchingMarket.abi')
    bin = Contract._load_bin(__name__, 'abi/MatchingMarket.bin')

    abi_support = Contract._load_abi(__name__, 'abi/MakerOtcSupportMethods.abi')

    def __init__(self, web3: Web3, address: Address, support_address: Optional[Address] = None):
        assert(isinstance(support_address, Address) or (support_address is None))

        super(MatchingMarket, self).__init__(web3=web3, address=address)

        self.support_address = support_address
        self._support_contract = self._get_contract(web3, self.abi_support, self.support_address) \
            if self.support_address else None

    @staticmethod
    def deploy(web3: Web3, close_time: int, support_address: Optional[Address] = None):
        """Deploy a new instance of the `MatchingMarket` contract.

        Args:
            web3: An instance of `Web` from `web3.py`.
            close_time: Unix timestamp of when the market will close.
            support_address: Ethereum address of the `MakerOtcSupportMethods` contract (optional).

        Returns:
            A `MatchingMarket` class instance.
        """
        return MatchingMarket(web3=web3, address=Contract._deploy(web3, MatchingMarket.abi, MatchingMarket.bin,
                                                                  [close_time]), support_address=support_address)

    def is_buy_enabled(self) -> bool:
        """Checks if direct buy is enabled.

        Returns:
            `True` if direct buy is enabled, `False` otherwise.
        """
        return self._contract.call().buyEnabled()

    def set_buy_enabled(self, buy_enabled: bool) -> Transact:
        """Enables or disables direct buy.

        Args:
            buy_enabled: Whether direct buy should be enabled or disabled.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(buy_enabled, bool))
        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'setBuyEnabled', [buy_enabled])

    def is_matching_enabled(self) -> bool:
        """Checks if order matching is enabled.

        Returns:
            `True` if order matching is enabled, `False` otherwise.
        """
        return self._contract.call().matchingEnabled()

    def set_matching_enabled(self, matching_enabled: bool) -> Transact:
        """Enables or disables order matching.

        Args:
            matching_enabled: Whether order matching should be enabled or disabled.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(matching_enabled, bool))
        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'setMatchingEnabled', [matching_enabled])

    def add_token_pair_whitelist(self, base_token: Address, quote_token: Address) -> Transact:
        """Adds a token pair to the whitelist.

        All newly created orders are checked against the whitelist.

        Args:
            base_token: Address of the ERC20 token.
            quote_token: Address of the ERC20 token.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(base_token, Address))
        assert(isinstance(quote_token, Address))

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'addTokenPairWhitelist', [base_token.address, quote_token.address])

    def get_orders(self, pay_token: Address = None, buy_token: Address = None) -> List[Order]:
        """Get all active orders.

        If both `pay_token` and `buy_token` are specified, orders will be filtered by these.
        In case of the _MatchingMarket_ implementation, order enumeration will be much efficient
        if these two parameters are supplied, as then orders can be fetched using `getBestOffer`
        and a series of `getWorseOffer` calls. This approach will result in much lower number of calls
        comparing to the naive 0..get_last_order_id approach, especially if the number of inactive orders
        is very high.

        Either none or both of these parameters have to be specified.

        Args:
            `pay_token`: Address of the `pay_token` to filter the orders by.
            `buy_token`: Address of the `buy_token` to filter the orders by.

        Returns:
            A list of `Order` objects representing all active orders on Oasis.
        """
        assert((isinstance(pay_token, Address) and isinstance(buy_token, Address))
               or (pay_token is None and buy_token is None))

        if pay_token is not None and buy_token is not None:
            orders = []

            if self._support_contract:
                result = self._support_contract.call().getOffers(self.address.address, pay_token.address, buy_token.address)

                while True:
                    count = 0
                    for i in range(0, 100):
                        if result[3][i] != '0x0000000000000000000000000000000000000000':
                            count += 1

                            orders.append(Order(market=self,
                                                order_id=result[0][i],
                                                maker=Address(result[3][i]),
                                                pay_token=pay_token,
                                                pay_amount=Wad(result[1][i]),
                                                buy_token=buy_token,
                                                buy_amount=Wad(result[2][i]),
                                                timestamp=result[4][i]))

                    if count == 100:
                        next_order_id = self._contract.call().getWorseOffer(orders[-1].order_id)
                        result = self._support_contract.call().getOffers(self.address.address, next_order_id)

                    else:
                        break

            else:
                order_id = self._contract.call().getBestOffer(pay_token.address, buy_token.address)
                while order_id != 0:
                    order = self.get_order(order_id)
                    if order is not None:
                        orders.append(order)

                    order_id = self._contract.call().getWorseOffer(order_id)

            return sorted(orders, key=lambda order: order.order_id)
        else:
            return super(ExpiringMarket, self).get_orders(pay_token, buy_token)

    def make(self, pay_token: Address, pay_amount: Wad, buy_token: Address, buy_amount: Wad, pos: int = None) -> Transact:
        """Create a new order.

        The `have_amount` of `have_token` token will be taken from you on order creation and deposited
        in the market contract. Allowance needs to be set first. Refer to the `approve()` method
        in the `ERC20Token` class.

        The `MatchingMarket` contract maintains an internal ordered linked list of orders, which allows the contract
        to do automated matching. Client placing a new order can either let the contract find the correct
        position in the linked list (by passing `0` as the `pos` argument of `make`) or calculate the position
        itself and just pass the right value to the contract (this will happen if you omit the `pos`
        argument of `make`). The latter should always use less gas. If the client decides not to calculate the
        position or it does get it wrong and the number of open orders is high at the same time, the new order
        may not even be placed at all as the attempt to calculate the position by the contract will likely fail
        due to high gas usage.

        When complete, `receipt.result` will contain order_id of the new order.

        Args:
            pay_token: Address of the ERC20 token you want to put on sale.
            pay_amount: Amount of the `pay_token` token you want to put on sale.
            buy_token: Address of the ERC20 token you want to be paid with.
            buy_amount: Amount of the `buy_token` you want to receive.
            pos: The position to insert the order at in the sorted list.
                If `None`, the optimal position will automatically get calculated.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(pay_token, Address))
        assert(isinstance(pay_amount, Wad))
        assert(isinstance(buy_token, Address))
        assert(isinstance(buy_amount, Wad))
        assert(isinstance(pos, int) or (pos is None))
        assert(pay_amount > Wad(0))
        assert(buy_amount > Wad(0))

        if pos is None:
            pos = self.position(pay_token=pay_token,
                                pay_amount=pay_amount,
                                buy_token=buy_token,
                                buy_amount=buy_amount)
        else:
            assert(pos >= 0)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'offer(uint256,address,uint256,address,uint256)',
                        [pay_amount.value, pay_token.address, buy_amount.value, buy_token.address, pos], None,
                        self._make_order_id_result_function)

    def position(self, pay_token: Address, pay_amount: Wad, buy_token: Address, buy_amount: Wad) -> int:
        """Calculate the position (`pos`) new order should be inserted at to minimize gas costs.

        The `MatchingMarket` contract maintains an internal ordered linked list of orders, which allows the contract
        to do automated matching. Client placing a new order can either let the contract find the correct
        position in the linked list (by passing `0` as the `pos` argument of `make`) or calculate the position
        itself and just pass the right value to the contract (this will happen if you omit the `pos`
        argument of `make`). The latter should always use less gas. If the client decides not to calculate the
        position or it does get it wrong and the number of open orders is high at the same time, the new order
        may not even be placed at all as the attempt to calculate the position by the contract will likely fail
        due to high gas usage.

        This method is responsible for calculating the correct insertion position. It is used internally
        by `make` when `pos` argument is omitted (or is `None`).

        Args:
            pay_token: Address of the ERC20 token you want to put on sale.
            pay_amount: Amount of the `pay_token` token you want to put on sale.
            buy_token: Address of the ERC20 token you want to be paid with.
            buy_amount: Amount of the `buy_token` you want to receive.

        Returns:
            The position (`pos`) new order should be inserted at.
        """
        assert(isinstance(pay_token, Address))
        assert(isinstance(pay_amount, Wad))
        assert(isinstance(buy_token, Address))
        assert(isinstance(buy_amount, Wad))

        self.logger.debug("Enumerating orders for position calculation...")

        orders = filter(lambda order: order.pay_amount / order.buy_amount >= pay_amount / buy_amount,
                        self.get_orders(pay_token, buy_token))

        self.logger.debug("Enumerating orders for position calculation finished")

        sorted_orders = sorted(orders, key=lambda o: o.pay_amount / o.buy_amount)
        return sorted_orders[0].order_id if len(sorted_orders) > 0 else 0

    def __repr__(self):
        return f"MatchingMarket('{self.address}')"
