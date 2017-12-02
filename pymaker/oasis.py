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
from typing import Optional, List

from web3 import Web3

from pymaker import Contract, Address, Transact
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
        sell_how_much: The amount of the `sell_which_token` token which is put on sale.
        sell_which_token: The address of the token which is put on sale.
        buy_how_much: The price the order creator wants to be paid, denominated in the `buy_which_token` token.
        buy_which_token: The address of the token the order creator wants to be paid with.
        owner: Ethereum address of the owner of this order.
        timestamp: Date and time when this order has been created, as a unix timestamp.
    """

    def __init__(self,
                 market,
                 order_id: int,
                 sell_how_much: Wad,
                 sell_which_token: Address,
                 buy_how_much: Wad,
                 buy_which_token: Address,
                 owner: Address,
                 timestamp: int):
        assert(isinstance(order_id, int))
        assert(isinstance(sell_how_much, Wad))
        assert(isinstance(sell_which_token, Address))
        assert(isinstance(buy_how_much, Wad))
        assert(isinstance(buy_which_token, Address))
        assert(isinstance(owner, Address))
        assert(isinstance(timestamp, int))

        self._market = market
        self.order_id = order_id
        self.sell_how_much = sell_how_much
        self.sell_which_token = sell_which_token
        self.buy_how_much = buy_how_much
        self.buy_which_token = buy_which_token
        self.owner = owner
        self.timestamp = timestamp

    @property
    def sell_to_buy_price(self) -> Wad:
        return self.sell_how_much / self.buy_how_much

    @property
    def buy_to_sell_price(self) -> Wad:
        return self.buy_how_much / self.sell_how_much

    @property
    def remaining_sell_amount(self) -> Wad:
        return self.sell_how_much

    def __eq__(self, other):
        assert(isinstance(other, Order))
        return self._market.address == other._market.address and self.order_id == other.order_id

    def __hash__(self):
        return self.order_id

    def __repr__(self):
        return pformat(vars(self))


class LogMake:
    def __init__(self, args):
        self.order_id = bytes_to_int(args['id'])
        self.maker = Address(args['maker'])
        self.pay_token = Address(args['pay_gem'])
        self.pay_amount = Wad(args['pay_amt'])
        self.buy_token = Address(args['buy_gem'])
        self.buy_amount = Wad(args['buy_amt'])
        self.timestamp = args['timestamp']

    def __repr__(self):
        return pformat(vars(self))


class LogBump:
    def __init__(self, args):
        self.order_id = bytes_to_int(args['id'])
        self.maker = Address(args['maker'])
        self.pay_token = Address(args['pay_gem'])
        self.pay_amount = Wad(args['pay_amt'])
        self.buy_token = Address(args['buy_gem'])
        self.buy_amount = Wad(args['buy_amt'])
        self.timestamp = args['timestamp']

    def __repr__(self):
        return pformat(vars(self))


class LogTake:
    def __init__(self, args):
        self.order_id = bytes_to_int(args['id'])
        self.maker = Address(args['maker'])
        self.taker = Address(args['taker'])
        self.pay_token = Address(args['pay_gem'])
        self.take_amount = Wad(args['take_amt'])
        self.buy_token = Address(args['buy_gem'])
        self.give_amount = Wad(args['give_amt'])
        self.timestamp = args['timestamp']

    def __repr__(self):
        return pformat(vars(self))


class LogKill:
    def __init__(self, args):
        self.order_id = bytes_to_int(args['id'])
        self.maker = Address(args['maker'])
        self.pay_token = Address(args['pay_gem'])
        self.pay_amount = Wad(args['pay_amt'])
        self.buy_token = Address(args['buy_gem'])
        self.buy_amount = Wad(args['buy_amt'])
        self.timestamp = args['timestamp']

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
        self._none_orders = set()

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

    def on_make(self, handler):
        assert(callable(handler))

        self._on_event(self._contract, 'LogMake', LogMake, handler)

    def on_bump(self, handler):
        assert(callable(handler))

        self._on_event(self._contract, 'LogBump', LogBump, handler)

    def on_take(self, handler):
        assert(callable(handler))

        self._on_event(self._contract, 'LogTake', LogTake, handler)

    def on_kill(self, handler):
        assert(callable(handler))

        self._on_event(self._contract, 'LogKill', LogKill, handler)

    def past_make(self, number_of_past_blocks: int) -> List[LogMake]:
        assert(isinstance(number_of_past_blocks, int))

        return self._past_events(self._contract, 'LogMake', LogMake, number_of_past_blocks)

    def past_bump(self, number_of_past_blocks: int) -> List[LogBump]:
        assert(isinstance(number_of_past_blocks, int))

        return self._past_events(self._contract, 'LogBump', LogBump, number_of_past_blocks)

    def past_take(self, number_of_past_blocks: int) -> List[LogTake]:
        assert(isinstance(number_of_past_blocks, int))

        return self._past_events(self._contract, 'LogTake', LogTake, number_of_past_blocks)

    def past_kill(self, number_of_past_blocks: int) -> List[LogKill]:
        assert(isinstance(number_of_past_blocks, int))

        return self._past_events(self._contract, 'LogKill', LogKill, number_of_past_blocks)

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

        # if an order is None, it won't become not-None again for the same OTC instance
        if order_id in self._none_orders:
            return None

        array = self._contract.call().offers(order_id)
        if array[5] is not True:
            self._none_orders.add(order_id)
            return None
        else:
            return Order(market=self,
                         order_id=order_id,
                         sell_how_much=Wad(array[0]),
                         sell_which_token=Address(array[1]),
                         buy_how_much=Wad(array[2]),
                         buy_which_token=Address(array[3]),
                         owner=Address(array[4]),
                         timestamp=array[6])

    def get_orders(self) -> List[Order]:
        orders = [self.get_order(order_id + 1) for order_id in range(self.get_last_order_id())]
        return [order for order in orders if order is not None]

    #TODO make it return the id of the newly created order
    def make(self, have_token: Address, have_amount: Wad, want_token: Address, want_amount: Wad) -> Transact:
        """Create a new order.

        The `have_amount` of `have_token` token will be taken from you on order creation and deposited
        in the market contract. Allowance needs to be set first - refer to the `approve()` method.

        Args:
            have_token: Address of the ERC20 token you want to put on sale.
            have_amount: Amount of the `have_token` token you want to put on sale.
            want_token: Address of the ERC20 token you want to be paid with.
            want_amount: Amount of the `want_token` you want to receive.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'make', [have_token.address, want_token.address, have_amount.value, want_amount.value])

    def bump(self, order_id: int) -> Transact:
        """Bumps an order.

        Bumping an order generates a `LogBump` event, which can make the order reappear
        in some front-ends relying on the events.

        Args:
            order_id: Id of the order you want to bump.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'bump',
                        [int_to_bytes32(order_id)])

    def take(self, order_id: int, quantity: Wad) -> Transact:
        """Takes (buys) an order.

        If `quantity` is equal to `sell_how_much`, the whole order will be taken (bought) which will make it
        disappear from the order book. If you want to buy a fraction of the order, set `quantity` to a number
        lower than `sell_how_much`.

        Args:
            order_id: Id of the order you want to take (buy).
            quantity: Quantity of `sell_which_token` that you want to buy.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
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
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kill', [int_to_bytes32(order_id)])

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

    def __repr__(self):
        return f"ExpiringMarket('{self.address}')"


class MatchingMarket(ExpiringMarket):
    """A client for a `MatchingMarket` contract.

    You can find the source code of the `OasisDEX` contracts here:
    <https://github.com/makerdao/maker-otc>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `MatchingMarket` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/MatchingMarket.abi')
    bin = Contract._load_bin(__name__, 'abi/MatchingMarket.bin')

    @staticmethod
    def deploy(web3: Web3, close_time: int):
        """Deploy a new instance of the `MatchingMarket` contract.

        Args:
            web3: An instance of `Web` from `web3.py`.
            close_time: Unix timestamp of when the market will close.

        Returns:
            A `MatchingMarket` class instance.
        """
        return MatchingMarket(web3=web3, address=Contract._deploy(web3, MatchingMarket.abi, MatchingMarket.bin,
                                                                  [close_time]))

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

    def make(self, have_token: Address, have_amount: Wad, want_token: Address, want_amount: Wad, pos: int = None) -> Transact:
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

        Args:
            have_token: Address of the ERC20 token you want to put on sale.
            have_amount: Amount of the `have_token` token you want to put on sale.
            want_token: Address of the ERC20 token you want to be paid with.
            want_amount: Amount of the `want_token` you want to receive.
            pos: The position to insert the order at in the sorted list.
                If `None`, the optimal position will automatically get calculated.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(have_token, Address))
        assert(isinstance(have_amount, Wad))
        assert(isinstance(want_token, Address))
        assert(isinstance(want_amount, Wad))
        assert(isinstance(pos, int) or (pos is None))
        assert(have_amount > Wad(0))
        assert(want_amount > Wad(0))

        if pos is None:
            pos = self.position(have_token=have_token,
                                have_amount=have_amount,
                                want_token=want_token,
                                want_amount=want_amount)
        else:
            assert(pos >= 0)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'offer', [have_amount.value, have_token.address, want_amount.value, want_token.address, pos])

    def position(self, have_token: Address, have_amount: Wad, want_token: Address, want_amount: Wad) -> int:
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
            have_token: Address of the ERC20 token you want to put on sale.
            have_amount: Amount of the `have_token` token you want to put on sale.
            want_token: Address of the ERC20 token you want to be paid with.
            want_amount: Amount of the `want_token` you want to receive.

        Returns:
            The position (`pos`) new order should be inserted at.
        """
        assert(isinstance(have_token, Address))
        assert(isinstance(have_amount, Wad))
        assert(isinstance(want_token, Address))
        assert(isinstance(want_amount, Wad))

        orders = filter(lambda o: o.sell_which_token == have_token and
                                  o.buy_which_token == want_token and
                                  o.sell_how_much / o.buy_how_much >= have_amount / want_amount, self.get_orders())

        sorted_orders = sorted(orders, key=lambda o: o.sell_how_much / o.buy_how_much)
        return sorted_orders[0].order_id if len(sorted_orders) > 0 else 0

    def __repr__(self):
        return f"MatchingMarket('{self.address}')"
