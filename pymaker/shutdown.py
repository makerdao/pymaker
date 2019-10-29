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
from pymaker.auctions import Flapper, Flipper, Flopper
from pymaker.logging import LogNote
from pymaker.numeric import Wad, Ray, Rad
from pymaker.token import DSToken, ERC20Token


logger = logging.getLogger()


class ShutdownModule(Contract):

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
        """Calls `cage` on the `end` contract"""
        logger.info("Calling fire to cage the end")
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'fire', [])


class EndContract:
    def __init__(self, web3: Web3, address: Address):
        pass
