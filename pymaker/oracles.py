# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 grandizzy
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
from pymaker.numeric import Wad


# TODO: Complete implementation and unit test
class OSM(Contract):
    """A client for the `OSM` contract.

    You can find the source code of the `OSM` contract here:
    <https://github.com/makerdao/osm>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `OSM` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/OSM.abi')
    bin = Contract._load_bin(__name__, 'abi/OSM.bin')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def poke(self) -> Transact:
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'poke', [])

    def peek(self) -> Wad:
        return Wad(self._extract_price(3))

    def peep(self) -> Wad:
        return Wad(self._extract_price(4))

    def zzz(self) -> int:
        return self._contract.functions.zzz().call()

    def _extract_price(self, storage_slot: int) -> int:
        assert isinstance(storage_slot, int)
        return Web3.toInt(self.web3.eth.getStorageAt(self.address.address, storage_slot)[16:])

    def __repr__(self):
        return f"OSM('{self.address}')"


class OldUniv2LpOSM(OSM):
    """A custom `OSM` contract for Uniswap LP tokens which used different storage slots, obsolete as of dss-1.7.0

    You can find the source code of the `OSM` contract here:
    <https://github.com/makerdao/univ2-lp-oracle>.
    """

    def __init__(self, web3: Web3, address: Address):
        super().__init__(web3, address)

    def peek(self) -> Wad:
        return Wad(self._extract_price(6))

    def peep(self) -> Wad:
        return Wad(self._extract_price(7))
