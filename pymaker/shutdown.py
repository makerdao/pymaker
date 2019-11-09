# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 EdNoepel
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

import logging
from datetime import datetime
from typing import Optional, List

from web3 import Web3

from web3.utils.events import get_event_data

from pymaker import Address, Contract, Transact
from pymaker.approval import directly, hope_directly
from pymaker.dss import Ilk
from pymaker.logging import LogNote
from pymaker.numeric import Wad, Ray, Rad
from pymaker.token import DSToken, ERC20Token


logger = logging.getLogger()


class ShutdownModule(Contract):
    """A client for the `ESM` contract, which allows users to call `end.cage()` and thereby trigger a shutdown.

    Ref. <https://github.com/makerdao/esm/blob/master/src/ESM.sol>

    Attributes:
      web3: An instance of `Web` from `web3.py`.
      address: Ethereum address of the `ESM` contract."""

    abi = Contract._load_abi(__name__, 'abi/ESM.abi')
    bin = Contract._load_bin(__name__, 'abi/ESM.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def sum(self) -> Wad:
        """Total balance of MKR `join`ed to this contract"""
        return Wad(self._contract.call().Sum())

    def sum_of(self, address: Address) -> Wad:
        """MKR `join`ed to this contract by a specific account"""
        assert isinstance(address, Address)

        return Wad(self._contract.call().sum(address.address))

    def min(self) -> Wad:
        """Minimum amount of MKR required to call `fire`"""
        return Wad(self._contract.call().min())

    def fired(self) -> bool:
        """True if `fire` has been called"""
        return bool(self._contract.call().fired())

    def join(self, value: Wad) -> Transact:
        """Before `fire` can be called, sufficient MKR must be `join`ed to this contract"""
        assert isinstance(value, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'join', [value.value])

    def fire(self):
        """Calls `cage` on the `end` contract, initiating a shutdown."""
        logger.info("Calling fire to cage the end")
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'fire', [])


class End(Contract):
    """A client for the `End` contract, used to orchestrate a shutdown.

    Ref. <https://github.com/makerdao/dss/blob/master/src/end.sol>

    Attributes:
      web3: An instance of `Web` from `web3.py`.
      address: Ethereum address of the `ESM` contract."""

    abi = Contract._load_abi(__name__, 'abi/End.abi')
    bin = Contract._load_bin(__name__, 'abi/End.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def live(self) -> bool:
        """False when caged, true when uncaged"""
        return self._contract.call().live() > 0

    def when(self) -> datetime:
        """Time of cage"""
        timestamp = self._contract.call().when()
        return datetime.utcfromtimestamp(timestamp)

    def wait(self) -> int:
        """Processing cooldown length, in seconds"""
        return int(self._contract.call().wait())

    def debt(self) -> Rad:
        """total outstanding dai following processing"""
        return Rad(self._contract.call().debt())

    def tag(self, ilk: Ilk) -> Ray:
        """Cage price for the collateral"""
        assert isinstance(ilk, Ilk)
        return Ray(self._contract.call().tag(ilk.toBytes()))

    def gap(self, ilk: Ilk) -> Wad:
        """Collateral shortfall (difference of debt and collateral"""
        assert isinstance(ilk, Ilk)
        return Wad(self._contract.call().gap(ilk.toBytes()))

    def art(self, ilk: Ilk) -> Wad:
        """Total debt for the collateral"""
        assert isinstance(ilk, Ilk)
        return Wad(self._contract.call().Art(ilk.toBytes()))

    def fix(self, ilk: Ilk) -> Ray:
        """Final cash price for the collateral"""
        assert isinstance(ilk, Ilk)
        return Ray(self._contract.call().fix(ilk.toBytes()))

    def bag(self, address: Address) -> Wad:
        """Amount of Dai `pack`ed for retrieving collateral in return"""
        assert isinstance(address, Address)
        return Wad(self._contract.call().bag(address.address))

    def out(self, ilk: Ilk, address: Address) -> Wad:
        assert isinstance(ilk, Ilk)
        assert isinstance(address, Address)
        return Wad(self._contract.call().out(ilk.toBytes(), address.address))

    def cage(self, ilk: Ilk) -> Transact:
        """Set the `cage` price for the collateral"""
        assert isinstance(ilk, Ilk)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'cage(bytes32)', [ilk.toBytes()])

    def skip(self, ilk: Ilk, flip_id: int) -> Transact:
        """Cancel a flip auction and seize it's collateral"""
        assert isinstance(ilk, Ilk)
        assert isinstance(flip_id, int)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'skip', [ilk.toBytes(), flip_id])

    def skim(self, ilk: Ilk, address: Address) -> Transact:
        """Cancels undercollateralized CDP debt to determine collateral shortfall"""
        assert isinstance(ilk, Ilk)
        assert isinstance(address, Address)
        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'skim', [ilk.toBytes(), address.address])

    def free(self, ilk: Ilk) -> Transact:
        """Releases excess collateral after `skim`ming"""
        assert isinstance(ilk, Ilk)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'free', [ilk.toBytes()])

    def thaw(self):
        """Fix the total outstanding supply of Dai"""
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'thaw', [])

    def flow(self, ilk: Ilk) -> Transact:
        """Calculate the `fix`, the cash price for a given collateral"""
        assert isinstance(ilk, Ilk)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'flow', [ilk.toBytes()])

    def pack(self, dai: Wad) -> Transact:
        """Deposit Dai into the `bag`, from which it cannot be withdrawn"""
        assert isinstance(dai, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'pack', [dai.value])

    def cash(self, ilk: Ilk, dai: Wad):
        """Exchange an amount of dai (already `pack`ed in the `bag`) for collateral"""
        assert isinstance(ilk, Ilk)
        assert isinstance(dai, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'cash', [ilk.toBytes(), dai.value])
