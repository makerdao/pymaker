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

from web3 import Web3

from pymaker import Contract, Address, Transact
from pymaker.auth import DSAuth


class DSValue(DSAuth):
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
    def deploy(web3: Web3):
        return DSValue(web3=web3, address=Contract._deploy(web3, DSValue.abi, DSValue.bin, []))

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

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
        return self._contract.call().read()

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

    def poke(self, new_value: bytes) -> Transact:
        """Populates this instance with a new value.

        Args:
            new_value: A 32-byte array with the new value to be set.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(new_value, bytes))
        assert(len(new_value) == 32)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'poke', [new_value])

    def poke_with_int(self, new_value: int) -> Transact:
        """Populates this instance with a new value.

        Handles the conversion of a Python `int` into the Solidity `bytes32` type automatically.

        If the value you want to set is actually a `Ray` or a `Wad`, you can get the integer value from them
        by accessing their `value` property. Please see `Ray` or `Wad` for more details.

        Args:
            new_value: A non-negative integer with the new value to be set.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(new_value, int))
        assert(new_value >= 0)
        return self.poke(new_value.to_bytes(32, byteorder='big'))

    def void(self) -> Transact:
        """Removes the current value from this instance.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'void', [])

    def __repr__(self):
        return f"DSValue('{self.address}')"
