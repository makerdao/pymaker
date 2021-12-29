# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2021 reverendus, EdNoepel
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
from pprint import pformat
from typing import Optional, Tuple
from web3 import Web3


class GasStrategy(object):
    GWEI = 1000000000

    """Abstract class, which can be inherited for implementing different gas price strategies.

    To build custom gas price strategies, override methods within such that gas fees returned 
    increase over time. The piece of code responsible for sending Ethereum transactions
    (please see :py:class:`pymaker.Transact`) will in this case overwrite the transaction
    with another one, using the same `nonce` but increasing gas price. If the value returned
    by `get_gas_price` does not go up, no new transaction gets submitted to the network.

    An example custom gas price strategy my be: start with 10 GWei. If transaction has not been
    confirmed within 10 minutes, try again with 15 GWei. If still no confirmation, increase
    to 30 GWei and then wait indefinitely for confirmation.
    """

    def get_gas_price(self, time_elapsed: int) -> Optional[int]:
        """Return gas price applicable for type 0 transactions.

        Bear in mind that Geth requires the gas price for overwritten transactions to increase by at
        least 10%, while OpenEthereum requires a gas price bump of 12.5%. Also, you may return
        `None` which will make the node use the default gas price, but once you returned
        a numeric value (gas price in Wei), you shouldn't switch back to `None` as such
        transaction will likely not get overwritten.

        Args:
            time_elapsed: Number of seconds since this specific Ethereum transaction
                has been originally sent for the first time.

        Returns:
            Gas price in Wei, or `None` if default gas price should be used. Default gas price
            means it's the Ethereum node the keeper is connected to will decide on the gas price.
        """
        raise NotImplementedError("Please implement this method")

    def get_gas_fees(self, time_elapsed: int) -> Tuple[int, int]:
        """Return max fee (fee cap) and priority fee (tip) for type 2 (EIP-1559) transactions.

        Note that Web3 currently requires specifying both `maxFeePerGas` and `maxPriorityFeePerGas` on a type 2
        transaction.  This is inconsistent with the EIP-1559 spec.

        Args:
            time_elapsed: Number of seconds since this specific Ethereum transaction
                has been originally sent for the first time.

        Returns:
            Gas price in Wei, or `None` if default gas price should be used. Default gas price
            means it's the Ethereum node the keeper is connected to will decide on the gas price.
        """
        raise NotImplementedError("Please implement this method")

    def __repr__(self):
        return f"{__name__}({pformat(vars(self))})"


class DefaultGasPrice(GasStrategy):
    """Default gas price.

    Uses the default gas price i.e. gas price will be decided by the Ethereum node
    the keeper is connected to.
    """

    def get_gas_price(self, time_elapsed: int) -> Optional[int]:
        return None

    def get_gas_fees(self, time_elapsed: int) -> Optional[Tuple[int, int]]:
        return None, None


class NodeAwareGasStrategy(GasStrategy):
    """Abstract baseclass which is Web3-aware.

    Retrieves the default gas price provided by the Ethereum node to be consumed by subclasses.
    """

    def __init__(self, web3: Web3):
        assert isinstance(web3, Web3)
        if self.__class__ == NodeAwareGasStrategy:
            raise NotImplementedError('This class is not intended to be used directly')
        self.web3 = web3

    def get_gas_price(self, time_elapsed: int) -> Optional[int]:
        """If user wants node to choose gas price, they should use DefaultGasPrice for the same functionality
        without an additional HTTP request.  This baseclass exists to let a subclass manipulate the node price."""
        raise NotImplementedError("Please implement this method")

    def get_gas_fees(self, time_elapsed: int) -> Optional[Tuple[int, int]]:
        """Implementation of tip is subjective.  For August 2021, the following implementation is a reasonable example:
        return int(self.get_next_base_fee(self)*1.5), 2 * self.GWEI"""
        raise NotImplementedError("Please implement this method")

    def get_node_gas_price(self) -> int:
        return max(self.web3.manager.request_blocking("eth_gasPrice", []), 1)

    def get_base_fee(self) -> Optional[int]:
        """Useful for calculating maxfee; a multiple of this value is suggested"""
        pending_block = self.web3.eth.get_block('pending')
        if 'baseFeePerGas' in pending_block:
            return max(int(pending_block['baseFeePerGas']), 1)
        else:
            return None


class FixedGasPrice(GasStrategy):
    """Fixed gas price.

    Uses specified gas price instead of the default price suggested by the Ethereum
    node the keeper is connected to. The gas price may be later changed (while the transaction
    is still in progress) by calling the `update_gas_price` method.

    Attributes:
        gas_price: Gas price to be used (in Wei) for legacy transactions
        max_fee:   Maximum fee (in Wei) for EIP-1559 transactions, should be >= (base_fee + tip)
        tip:       Priority fee (in Wei) for EIP-1559 transactions
    """
    def __init__(self, gas_price: Optional[int], max_fee: Optional[int] = None, tip: Optional[int] = None):
        assert isinstance(gas_price, int) or gas_price is None
        assert isinstance(max_fee, int) or max_fee is None
        assert isinstance(tip, int) or tip is None
        assert gas_price or (max_fee and tip)
        self.gas_price = gas_price
        self.max_fee = max_fee
        self.tip = tip

    def update_gas_price(self, new_gas_price: int, new_max_fee: int, new_tip: int):
        """Changes the initial gas price to a higher value, preferably higher.

        The only reason when calling this function makes sense is when an async transaction is in progress.
        In this case, the loop waiting for the transaction to be mined (see :py:class:`pymaker.Transact`)
        will resend the pending transaction again with the new gas price.

        As OpenEthereum excepts the gas price to rise by at least 12.5% in replacement transactions, the price
        argument supplied to this method should be accordingly higher.

        Args:
            new_gas_price:  New gas price to be set (in Wei).
            new_max_fee:    New maximum fee (in Wei) appropriate for subsequent block(s).
            new_tip:        New prioritization fee (in Wei).
        """
        assert isinstance(new_gas_price, int) or new_gas_price is None
        assert isinstance(new_max_fee, int) or new_max_fee is None
        assert isinstance(new_tip, int) or new_tip is None
        assert new_gas_price or (new_max_fee and new_tip)
        self.gas_price = new_gas_price
        self.max_fee = new_max_fee
        self.tip = new_tip

    def get_gas_price(self, time_elapsed: int) -> Optional[int]:
        return self.gas_price

    def get_gas_fees(self, time_elapsed: int) -> Optional[Tuple[int, int]]:
        return self.max_fee, self.tip


class GeometricGasPrice(NodeAwareGasStrategy):
    """Geometrically increasing gas price.

    Start with `initial_price`, then increase it every 'every_secs' seconds by a fixed coefficient.
    Coefficient defaults to 1.125 (12.5%), the minimum increase for OpenEthereum to replace a transaction.
    Coefficient can be adjusted, and there is an optional upper limit.

    To disable legacy (type 0) transactions, set initial_price None.
    To disable EIP-1559 (type 2) transactions, set initial_tip None.
    Other parameters apply to both transaction types.

    Attributes:
        initial_price: The initial gas price in Wei, used only for legacy transactions.
        initial_tip: Initial priority fee paid on top of a base fee (recommend 1 GWEI minimum).
        every_secs: Gas increase interval (in seconds).
        coefficient: Gas price and tip multiplier, defaults to 1.125.
        max_price: Optional upper limit and fee cap, defaults to None.
    """
    def __init__(self, web3: Web3, initial_price: Optional[int], initial_tip: Optional[int],
                 every_secs: int, coefficient=1.125, max_price: Optional[int] = None):
        assert isinstance(web3, Web3)
        assert (isinstance(initial_price, int) and initial_price > 0) or initial_price is None
        assert isinstance(initial_tip, int) or initial_tip is None
        assert initial_price or (initial_tip is not None and initial_tip > 0)
        assert isinstance(every_secs, int)
        assert isinstance(coefficient, float)
        assert (isinstance(max_price, int) and max_price > 0) or max_price is None
        assert every_secs > 0
        assert coefficient > 1
        if initial_price and max_price:
            assert initial_price <= max_price
        if initial_tip and max_price:
            assert initial_tip < max_price
        super().__init__(web3)

        self.initial_price = initial_price
        self.initial_tip = initial_tip
        self.every_secs = every_secs
        self.coefficient = coefficient
        self.max_price = max_price

    def scale_by_time(self, value: int, time_elapsed: int) -> int:
        assert isinstance(value, int)
        assert isinstance(time_elapsed, int)
        result = value
        if time_elapsed >= self.every_secs:
            for second in range(math.floor(time_elapsed / self.every_secs)):
                result *= self.coefficient
        return math.ceil(result)

    def get_gas_price(self, time_elapsed: int) -> Optional[int]:
        assert isinstance(time_elapsed, int)
        if not self.initial_price:
            return None

        result = self.scale_by_time(self.initial_price, time_elapsed)
        if self.max_price is not None:
            result = min(result, self.max_price)

        return result

    def get_gas_fees(self, time_elapsed: int) -> Optional[Tuple[int, int]]:
        assert isinstance(time_elapsed, int)
        if not self.initial_tip:
            return None, None

        base_fee = self.get_base_fee()
        if not base_fee:
            raise RuntimeError("Node does not provide baseFeePerGas; type 2 transactions are not available")

        tip = self.scale_by_time(self.initial_tip, time_elapsed)

        # This is how it should work, but doesn't; read more here: https://github.com/ethereum/go-ethereum/issues/23311
        # if self.max_price:
        #     # If the scaled tip would exceed our fee cap, reduce tip to largest possible
        #     if base_fee + tip > self.max_price:
        #         tip = max(0, self.max_price - base_fee)
        #     # Honor the max_price, even if it does not exceed base fee
        #     return self.max_price, tip
        # else:
        #     # If not limited by user, set a standard fee cap of twice the base fee with tip included
        #     return (base_fee * 2) + tip, tip

        # HACK: Ensure both feecap and tip are scaled, satisfying geth's current replacement logic.
        feecap = self.scale_by_time(int(base_fee * 1.2), time_elapsed) + tip
        if self.max_price and feecap > self.max_price:
            feecap = self.max_price
        return feecap, min(tip, feecap)
