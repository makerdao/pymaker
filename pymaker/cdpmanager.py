
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
from pymaker import Address, Contract, Transact
from pymaker.dss import Ilk, Urn, Vat
from pymaker.numeric import Wad


class CdpManager(Contract):
    """A client for the `DSCdpManger` contract, which is a wrapper around the cdp system, for easier use.

    Ref. <https://github.com/makerdao/dss-cdp-manager/blob/master/src/DssCdpManager.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/DssCdpManager.abi')
    bin = Contract._load_bin(__name__, 'abi/DssCdpManager.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)
        self.vat = Vat(self.web3, Address(self._contract.functions.vat().call()))

    def open(self, ilk: Ilk, address: Address) -> Transact:
        assert isinstance(ilk, Ilk)
        assert isinstance(address, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'open',
                        [ilk.toBytes(), address.address])

    def urn(self, cdpid: int) -> Urn:
        '''Returns Urn for respective CDP ID'''
        assert isinstance(cdpid, int)

        urn_address = Address(self._contract.functions.urns(cdpid).call())
        ilk = self.ilk(cdpid)
        urn = self.vat.urn(ilk, Address(urn_address))

        return urn

    def owns(self, cdpid: int) -> Address:
        '''Returns owner Address of respective CDP ID'''
        assert isinstance(cdpid, int)

        owner = Address(self._contract.functions.owns(cdpid).call())
        return owner

    def ilk(self, cdpid: int) -> Ilk:
        '''Returns Ilk for respective CDP ID'''
        assert isinstance(cdpid, int)

        ilk = Ilk.fromBytes(self._contract.functions.ilks(cdpid).call())
        return ilk

    def first(self, address: Address) -> int:
        '''Returns first CDP Id created by owner address'''
        assert isinstance(address, Address)

        cdpid = int(self._contract.functions.first(address.address).call())
        return cdpid

    def last(self, address: Address) -> int:
        '''Returns last CDP Id created by owner address'''
        assert isinstance(address, Address)

        cdpid = self._contract.functions.last(address.address).call()
        return int(cdpid)

    def count(self, address: Address) -> int:
        '''Returns number of CDP's created using the DS-Cdp-Manager contract specifically'''
        assert isinstance(address, Address)

        count = int(self._contract.functions.count(address.address).call())
        return count

    def __repr__(self):
        return f"CdpManager('{self.address}')"
