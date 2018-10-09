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
from pymaker.dss import Urn, Ilk
from pymaker.numeric import Wad


class GemMock(Contract):
    """A client for `GemMock` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/GemMock.abi')
    bin = Contract._load_bin(__name__, 'abi/GemMock.bin')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3, vat: Address, ilk: Ilk, gem: Address):
        assert isinstance(web3, Web3)
        assert isinstance(vat, Address)
        assert isinstance(ilk, Ilk)
        assert isinstance(gem, Address)

        return GemMock(web3=web3, address=Contract._deploy(web3, GemMock.abi, GemMock.bin, [vat.address,
                                                                                            ilk.toBytes(),
                                                                                            gem.address]))
    def ilk(self):
        return Ilk.fromBytes(self._contract.call().ilk())

    def join(self, urn: Urn, value: Wad) -> Transact:
        assert(isinstance(urn, Urn))
        assert(isinstance(value, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'join', [urn.toBytes() , value.value])

    def hope(self, guy: Address) -> Transact:
        assert(isinstance(guy, Address))

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'hope', [guy.address])

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"GemMock('{self.address}')"
