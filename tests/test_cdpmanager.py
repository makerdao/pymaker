# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2020 EdNoepel
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

from pymaker import Address
from pymaker.cdpmanager import CdpManager, Urn
from tests.conftest import mcd, web3


class TestCdpManager:
    def setup_class(self):
        dss_deployment = mcd(web3())
        self.ilk = dss_deployment.collaterals['ETH-A'].ilk
        self.cdpmanager = CdpManager(web3(), Address("0x32Ee2bF1267253f76298D4199095B9C6b5A389c0"))

    def test_none(self, our_address):
        assert self.cdpmanager.first(our_address) == 0
        assert self.cdpmanager.last(our_address) == 0
        assert self.cdpmanager.count(our_address) == 0

    def test_open(self, our_address):
        assert self.cdpmanager.open(self.ilk, our_address).transact()
        assert self.cdpmanager.last(our_address) == 1
        assert self.cdpmanager.ilk(1).name == self.ilk.name
        assert self.cdpmanager.owns(1) == our_address
        assert isinstance(self.cdpmanager.urn(1), Urn)

    def test_one(self, our_address):
        assert self.cdpmanager.first(our_address) == 1
        assert self.cdpmanager.last(our_address) == 1
        assert self.cdpmanager.count(our_address) == 1
