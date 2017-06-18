# This file is part of "maker.py".
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

from api.Address import Address
from api.Contract import Contract
from api.Receipt import Receipt


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

    abi = Contract._load_abi(__name__, 'DSValue.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def has_value(self) -> bool:
        """Checks whether this instance of `DSValue` contains a value.

        Returns:
            `True` if this instance contains a value, which can be read. `False` otherwise.
        """
        return self._contract.call().peek()[1]

    def read(self) -> bytes:
        """Reads the current value from this `DSValue` instance as a byte array.

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

        If the value is actually a `Ray` or a `Wad`, you can convert it to one using `Ray.from_uint(...)`
        or `Wad.from_uint(...)`. Please see `Ray` or `Wad` for more details.

        If this instance does not contain a value, throws an exception.

        Returns:
            An integer representation of the current value of this instance.
        """
        return int(self.read_as_hex(), 16)

    def poke(self, new_value: bytes) -> Optional[Receipt]:
        """Populated this `DSValue` instance with a new value.

        Args:
            new_value: A 32-byte array with the new value to be set.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the value has been set.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(new_value, bytes))
        assert(len(new_value) == 32)
        try:
            tx_hash = self._contract.transact().poke(new_value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def poke_with_int(self, new_value: int) -> Optional[Receipt]:
        """Populate this `DSValue` instance with a new value.

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
        """Removes the current value from this `DSValue` instance.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the value has been removed.
            `None` if the Ethereum transaction failed.
        """
        try:
            tx_hash = self._contract.transact().void()
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    #TODO as web3.py doesn't seem to support anonymous events, monitoring for LogNote events does not work
    # def watch(self):
    #     self._contract.on("LogNote", {'filter': {'sig': bytearray.fromhex('1504460f')}}, self.__note)
    #     self._contract.pastEvents("LogNote", {'fromBlock': 0, 'filter': {'sig': bytearray.fromhex('1504460f')}}, self.__note)
    #
    #     # 'topics': ['0x1504460f00000000000000000000000000000000000000000000000000000000']
    #     # 'topics': ['0x1504460f00000000000000000000000000000000000000000000000000000000']
    #
    # def __note(self, log):
    #     args = log['args']
    #     print(args)



