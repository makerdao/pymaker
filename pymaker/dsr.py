# This file is part of Maker Keeper Framework.
#
# Copyright (C)2019 grandizzy
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


from pymaker import Address, Transact, Calldata
from pymaker.numeric import Wad, Ray
from pymaker.proxy import DSProxy
from pymaker.deployment import DssDeployment


logger = logging.getLogger()


class Dsr:
    """ DSR Client implementation
    """

    _ZERO_ADDRESS = Address("0x0000000000000000000000000000000000000000")

    def __init__(self, mcd: DssDeployment, owner: Address):
        assert (isinstance(mcd, DssDeployment))
        assert (isinstance(owner, Address))

        self.owner = owner
        self.mcd = mcd

    def has_proxy(self) -> bool:
        return self.mcd.proxy_registry.proxies(self.owner) != self._ZERO_ADDRESS

    def get_proxy(self) -> DSProxy:
        return DSProxy(self.mcd.web3, Address(self.mcd.proxy_registry.proxies(self.owner)))

    def build_proxy(self) -> Transact:
        return self.mcd.proxy_registry.build(self.owner)

    def chi(self) -> Ray:
        return self.mcd.pot.chi()

    def get_total_dai(self) -> Wad:
        return self.mcd.pot.pie() * self.chi()

    def dsr(self) -> Ray:
        return self.mcd.pot.dsr()

    def get_balance(self, proxy: Address) -> Wad:
        assert (isinstance(proxy, Address))

        total_pie = self.mcd.pot.pie()
        if total_pie == Wad.from_number(0):
            return Wad.from_number(0)

        slice = self.mcd.pot.pie_of(proxy)
        portion = slice / total_pie
        dai_in_pot = self.mcd.vat.dai(self.mcd.pot.address)

        return Wad((dai_in_pot * portion) * self.chi())

    def join(self, amount: Wad, proxy: DSProxy) -> Transact:
        assert (isinstance(amount, Wad))
        assert (isinstance(proxy, DSProxy))

        return proxy.execute_at(self.mcd.dss_proxy_actions.address,
                                Calldata.from_signature(
                                    "join(address,address,uint256)",
                                    [
                                        self.mcd.dai_adapter.address.address,
                                        self.mcd.pot.address.address,
                                        amount.value
                                    ])
                                )

    def exit(self, amount: Wad, proxy: DSProxy) -> Transact:
        assert (isinstance(amount, Wad))
        assert (isinstance(proxy, DSProxy))

        return proxy.execute_at(self.mcd.dss_proxy_actions.address,
                                Calldata.from_signature(
                                    "exit(address,address,uint256)",
                                    [
                                        self.mcd.dai_adapter.address.address,
                                        self.mcd.pot.address.address,
                                        amount.value
                                    ])
                                )

    def exit_all(self, proxy: DSProxy) -> Transact:
        assert (isinstance(proxy, DSProxy))

        return proxy.execute_at(self.mcd.dss_proxy_actions.address,
                                Calldata.from_signature(
                                    "exitAll(address,address)",
                                    [
                                        self.mcd.dai_adapter.address.address,
                                        self.mcd.pot.address.address
                                    ])
                                )
