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

import math
from typing import Optional


class GasPrice(object):
    """Abstract class, which can be inherited for implementing different gas price strategies.

    `GasPrice` class contains only one method, `get_gas_price`, which is responsible for
    returning the gas price (in Wei) for a specific point in time. It is possible to build
    custom gas price strategies by implementing this method so the gas price returned
    increases over time. The piece of code responsible for sending Ethereum transactions
    (please see :py:class:`pymaker.Transact`) will in this case overwrite the transaction
    with another one, using the same `nonce` but increasing gas price. If the value returned
    by `get_gas_price` does not go up, no new transaction gets submitted to the network.

    An example custom gas price strategy my be: start with 10 GWei. If transaction has not been
    confirmed within 10 minutes, try again with 15 GWei. If still no confirmation, increase
    to 30 GWei and then wait indefinitely for confirmation.
    """

    def get_gas_price(self, time_elapsed: int) -> Optional[int]:
        """Return gas price applicable for a given point in time.

        Bear in mind that Parity (don't know about other Ethereum nodes) requires the gas
        price for overwritten transactions to go up by at least 10%. Also, you may return
        `None` which will make the node use the default gas price, but once you returned
        a numeric value (gas price in Wei), you shouldn't switch back to `None` as such
        transaction also may not get properly overwritten.

        Args:
            time_elapsed: Number of seconds since this specific Ethereum transaction
                has been originally sent for the first time.

        Returns:
            Gas price in Wei, or `None` if default gas price should be used. Default gas price
            means it's the Ethereum node the keeper is connected to will decide on the gas price.
        """
        raise NotImplementedError("Please implement this method")


class DefaultGasPrice(GasPrice):
    """Default gas price.

    Uses the default gas price i.e. gas price will be decided by the Ethereum node
    the keeper is connected to.
    """

    def get_gas_price(self, time_elapsed: int) -> Optional[int]:
        return None


class FixedGasPrice(GasPrice):
    """Fixed gas price.

    Uses specified gas price instead of the default price suggested by the Ethereum
    node the keeper is connected to. The gas price may be later changed (while the transaction
    is still in progress) by calling the `update_gas_price` method.

    Attributes:
        gas_price: Gas price to be used (in Wei).
    """
    def __init__(self, gas_price: int):
        assert(isinstance(gas_price, int))
        self.gas_price = gas_price

    def update_gas_price(self, new_gas_price: int):
        """Changes the initial gas price to a higher value, preferably higher.

        The only reason when calling this function makes sense is when an async transaction is in progress.
        In this case, the loop waiting for the transaction to be mined (see :py:class:`pymaker.Transact`)
        will resend the pending transaction again with the new gas price.

        As Parity excepts the gas price to rise by at least 10% in replacement transactions, the price
        argument supplied to this method should be accordingly higher.

        Args:
            new_gas_price: New gas price to be set (in Wei).
        """
        assert(isinstance(new_gas_price, int))

        self.gas_price = new_gas_price

    def get_gas_price(self, time_elapsed: int) -> Optional[int]:
        assert(isinstance(time_elapsed, int))
        return self.gas_price


class IncreasingGasPrice(GasPrice):
    """Constantly increasing gas price.

    Start with `initial_price`, then increase it by fixed amount `increase_by` every `every_secs` seconds
    until the transaction gets confirmed. There is an optional upper limit.

    Attributes:
        initial_price: The initial gas price in Wei i.e. the price the transaction
            is originally sent with.
        increase_by: Gas price increase in Wei, which will happen every `every_secs` seconds.
        every_secs: Gas price increase interval (in seconds).
        max_price: Optional upper limit.
    """
    def __init__(self, initial_price: int, increase_by: int, every_secs: int, max_price: Optional[int]):
        assert(isinstance(initial_price, int))
        assert(isinstance(increase_by, int))
        assert(isinstance(every_secs, int))
        assert(isinstance(max_price, int) or max_price is None)
        assert(initial_price > 0)
        assert(increase_by > 0)
        assert(every_secs > 0)
        if max_price is not None:
            assert(max_price > 0)

        self.initial_price = initial_price
        self.increase_by = increase_by
        self.every_secs = every_secs
        self.max_price = max_price

    def get_gas_price(self, time_elapsed: int) -> Optional[int]:
        assert(isinstance(time_elapsed, int))

        result = self.initial_price + int(time_elapsed/self.every_secs)*self.increase_by
        if self.max_price is not None:
            result = min(result, self.max_price)

        return result


class GeometricGasPrice(GasPrice):
    """Geometrically increasing gas price.

    Start with `initial_price`, then increase it every 'every_secs' seconds by a fixed coefficient.
    Coefficient defaults to 1.125 (12.5%), the minimum increase for Parity to replace a transaction.
    Coefficient can be adjusted, and there is an optional upper limit.

    Attributes:
        initial_price: The initial gas price in Wei i.e. the price the transaction is originally sent with.
        every_secs: Gas price increase interval (in seconds).
        coefficient: Gas price multiplier, defaults to 1.125.
        max_price: Optional upper limit, defaults to None.
    """
    def __init__(self, initial_price: int, every_secs: int, coefficient=1.125, max_price: Optional[int] = None):
        assert (isinstance(initial_price, int))
        assert (isinstance(every_secs, int))
        assert (isinstance(max_price, int) or max_price is None)
        assert (initial_price > 0)
        assert (every_secs > 0)
        assert (coefficient > 1)
        if max_price is not None:
            assert(max_price > 0)

        self.initial_price = initial_price
        self.every_secs = every_secs
        self.coefficient = coefficient
        self.max_price = max_price

    def get_gas_price(self, time_elapsed: int) -> Optional[int]:
        assert(isinstance(time_elapsed, int))

        if time_elapsed < self.every_secs:
            return self.initial_price
        result = self.initial_price
        for second in range(math.floor(time_elapsed/self.every_secs)):
            result *= self.coefficient
        if self.max_price is not None:
            result = min(result, self.max_price)

        return math.ceil(result)
