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
from pymaker.deployment import DssDeployment
from pymaker.cdpmanager import Urn


class TestCdpManager:

    def test_none(self, our_address: Address, mcd: DssDeployment):
        assert mcd.cdp_manager.first(our_address) == 0
        assert mcd.cdp_manager.last(our_address) == 0
        assert mcd.cdp_manager.count(our_address) == 0

    def test_open(self, our_address: Address, mcd: DssDeployment):
        ilk = mcd.collaterals['ETH-A'].ilk
        assert mcd.cdp_manager.open(ilk, our_address).transact()
        assert mcd.cdp_manager.last(our_address) == 1
        assert mcd.cdp_manager.ilk(1).name == ilk.name
        assert mcd.cdp_manager.owns(1) == our_address
        assert isinstance(mcd.cdp_manager.urn(1), Urn)

    def test_one(self, our_address: Address, mcd: DssDeployment):
        assert mcd.cdp_manager.first(our_address) == 1
        assert mcd.cdp_manager.last(our_address) == 1
        assert mcd.cdp_manager.count(our_address) == 1
