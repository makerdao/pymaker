
# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2020 ith-harvey
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
from pymaker import Address, Contract
from pymaker.dss import Ilk, Vat
from pymaker.numeric import Wad


class CdpManager(Contract):
    """A client for the `DSCdpManger` contract, which is a wrapper around the cdp system, for easier use.

    Ref. <https://github.com/makerdao/dss-cdp-manager/blob/master/src/DssCdpManager.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/DSCdpManager.abi')
    bin = Contract._load_bin(__name__, 'abi/DSCdpManager.bin')


    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)
        self.vat = Vat(self.web3, Address(self._contract.call().vat()))

    def urn(self, cdpid):
        assert isinstance(int, cdpid)

        urn_address = Address(self._contract.call().urns(cdpid))
        ilk = self.ilk(cdpid)
        urn = self.vat.urn(ilk, Address(urn_address))

        return urn

    def list(self, cdpid) -> list:
        assert isinstance(int, cdpid)

        cdpid_list = self._contract.call().list(cdpid)
        return cdpid_list

    def owns(self, cdpid) -> Address:
        assert isinstance(int, cdpid)

        owner = Address(self._contract.call().owns(cdpid))
        return owner

    def ilk(self, cdpid) -> Ilk:
        assert isinstance(int, cdpid)

        ilk = Ilk.fromBytes(self._contract.call().ilks(cdpid))
        return ilk

    def first(self, address: Address):
        assert isinstance(address, Address)

        cdpid = self._contract.call().first(address.address)
        return cdpid

    def last(self, address: Address):
        assert isinstance(address, Address)

        cdpid = self._contract.call().last(address.address)
        return cdpid

    def count(self, address: Address) -> Wad:
        assert isinstance(address, Address)

        count = Wad.from_number(self._contract.call().count(address.address))
        return count

    def __repr__(self):
        return f"CdpManager('{self.address}')"





