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

from typing import Optional

import array
from web3 import Web3

from api import Contract, Address, Receipt


class DSValue(Contract):
    """A client for the `DSValue` contract, a single-value data feed.

    `DSValue` is a single-value data feed, which means it can be in one of two states.
    It can either contain a value (in which case `has_value()` returns `True` and the read methods
    return that value) or be empty (in which case `has_value()` returns `False` and the read
    methods throw exceptions).

    `DSValue` can be populated with a new value using `poke()` and cleared using `void()`.

    Everybody can read from a `DSValue`.
    Calling `poke()` and `void()` is usually whitelisted to some addresses only.

    The `DSValue` contract keeps the value as a 32-byte array (Ethereum `bytes32` type).
    Methods have been provided to cast it into `int`, read as hex etc.

    You can find the source code of the `DSValue` contract here:
    <https://github.com/dapphub/ds-value>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSValue` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSValue.abi')
    bin = Contract._load_bin(__name__, 'abi/DSValue.bin')

    @staticmethod
    def deploy(web3: Web3, *args):
        contract_factory = web3.eth.contract(abi=DSValue.abi, bytecode=DSValue.bin)
        tx_hash = contract_factory.deploy(args=args)
        receipt = web3.eth.getTransactionReceipt(tx_hash)
        return DSValue(web3=web3, address=Address(receipt['contractAddress']))

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def has_value(self) -> bool:
        """Checks whether this instance contains a value.

        Returns:
            `True` if this instance contains a value, which can be read. `False` otherwise.
        """
        return self._contract.call().peek()[1]

    def read(self) -> bytes:
        """Reads the current value from this instance as a byte array.

        If this instance does not contain a value, throws an exception.

        Returns:
            A 32-byte array with the current value of this instance.
        """
        read_value = self._contract.call().read()
        return array.array('B', [ord(x) for x in read_value]).tostring()

    def read_as_hex(self) -> str:
        """Reads the current value from this instance and converts it to a hex string.

        If this instance does not contain a value, throws an exception.

        Returns:
            A string with a hexadecimal representation of the current value of this instance.
        """
        return ''.join(hex(x)[2:].zfill(2) for x in self.read())

    def read_as_int(self) -> int:
        """Reads the current value from this instance and converts it to an int.

        If the value is actually a `Ray` or a `Wad`, you can convert it to one using `Ray(...)`
        or `Wad(...)`. Please see `Ray` or `Wad` for more details.

        If this instance does not contain a value, throws an exception.

        Returns:
            An integer representation of the current value of this instance.
        """
        return int(self.read_as_hex(), 16)

    def poke(self, new_value: bytes) -> Optional[Receipt]:
        """Populates this instance with a new value.

        Args:
            new_value: A 32-byte array with the new value to be set.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the value has been set.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(new_value, bytes))
        assert(len(new_value) == 32)
        return self._transact(self.web3, f"DSValue('{self.address}').poke('{new_value}')",
                              lambda: self._contract.transact().poke(new_value))

    def poke_with_int(self, new_value: int) -> Optional[Receipt]:
        """Populates this instance with a new value.

        Handles the conversion of a Python `int` into the Solidity `bytes32` type automatically.

        If the value you want to set is actually a `Ray` or a `Wad`, you can get the integer value from them
        by accessing their `value` property. Please see `Ray` or `Wad` for more details.

        Args:
            new_value: A non-negative integer with the new value to be set.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the value has been set.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(new_value, int))
        assert(new_value >= 0)
        return self.poke(new_value.to_bytes(32, byteorder='big'))

    def void(self) -> Optional[Receipt]:
        """Removes the current value from this instance.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the value has been removed.
            `None` if the Ethereum transaction failed.
        """
        return self._transact(self.web3, f"DSValue('{self.address}').void()",
                              lambda: self._contract.transact().void())


class DSCache(DSValue):
    """A client for the `DSCache` contract, an expiring single-value data feed.

    As `DSCache` inherits from `DSValue`, it replicates most of its features and methods.

    You can find the source code of the `DSCache` contract here:
    <https://github.com/dapphub/ds-cache>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSCache` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSCache.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    #TODO implement prod() method