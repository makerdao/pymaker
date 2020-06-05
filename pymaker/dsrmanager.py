
# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2020 kentonprescott
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
from pymaker.dss import Pot, DaiJoin
from pymaker.numeric import Wad, Rad
from pymaker.token import DSToken


class DsrManager(Contract):
    """
    A client for the `DsrManger` contract, which reduces the need for proxies
    when interacting with the Pot contract.

    Ref. <https://github.com/makerdao/dsr-manager/blob/master/src/DsrManager.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/DsrManager.abi')
    bin = Contract._load_bin(__name__, 'abi/DsrManager.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def pot(self) -> Pot:
        address = Address(self._contract.functions.pot().call())
        return Pot(self.web3, address)

    def dai(self) -> DSToken:
        address = Address(self._contract.functions.dai().call())
        return DSToken(self.web3, address)

    def dai_join(self) -> DaiJoin:
        address = Address(self._contract.functions.dai_join().call())
        return DaiJoin(self.web3, address)

    def supply(self) -> Wad:
        """Total supply of pie locked in Pot through DsrManager"""
        return Wad(self._contract.functions.supply().call())

    def pieOf(self, usr: Address) -> Wad:
        """Pie balance of a given usr address"""
        assert isinstance(usr, Address)

        return Wad(self._contract.functions.pieOf(usr.address).call())

    def daiOf(self, usr: Address) -> Rad:
        """
        Internal Dai balance of a given usr address - current Chi is used
        i.e. Dai balance potentially stale
        """
        assert isinstance(usr, Address)

        pie = self.pieOf(usr)
        chi = Pot(self.pot).chi()

        dai = Rad(pie * chi)

        return dai

    def join(self, dst: Address, dai: Wad) -> Transact:
        """Lock a given amount of ERC20 Dai into the DSR Contract and give to dst address """
        assert isinstance(dst, Address)
        assert isinstance(dai, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'join',
                        [dst.address, dai.value])

    def exit(self, dst: Address, dai: Wad) -> Transact:
        """ Free a given amount of ERC20 Dai from the DSR Contract and give to dst address """
        assert isinstance(dst, Address)
        assert isinstance(dai, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'exit',
                        [dst.address, dai.value])

    def exitAll(self, dst: Address) -> Transact:
        """ Free all ERC20 Dai from the DSR Contract and give to dst address """
        assert isinstance(dst, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'exitAll', [dst.address])

    def __repr__(self):
        return f"DsrManager('{self.address}')"
