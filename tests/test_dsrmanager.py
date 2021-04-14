# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2020 Maker Ecosystem Growth Holdings, INC
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

import pytest
from pymaker import Address
from tests.helpers import time_travel_by
from pymaker.numeric import Wad, Rad, Ray
from pymaker.deployment import DaiJoin, DssDeployment
from pymaker.dss import Pot
from pymaker.token import DSToken
from tests.test_dss import wrap_eth, frob


def mint_dai(mcd: DssDeployment, amount: Wad, ilkName: str, our_address: Address):
    startingAmount = mcd.dai.balance_of(our_address)
    dai = amount
    # Add collateral to our CDP and draw internal Dai
    collateral=mcd.collaterals[ilkName]
    ilk = mcd.vat.ilk(collateral.ilk.name)
    dink = Wad.from_number(1)
    dart = Wad( Rad(dai) / Rad(ilk.rate))
    wrap_eth(mcd, our_address, dink)
    assert collateral.gem.balance_of(our_address) >= dink
    assert collateral.gem.approve(collateral.adapter.address).transact(from_address=our_address)
    assert collateral.adapter.join(our_address, dink).transact(from_address=our_address)
    frob(mcd, collateral, our_address, dink=dink, dart=dart)

    # Exit to Dai Token and make some checks
    assert mcd.vat.hope(mcd.dai_adapter.address).transact(from_address=our_address)
    assert mcd.dai_adapter.exit(our_address, dai).transact(from_address=our_address)
    assert mcd.dai.balance_of(our_address) == dai + startingAmount


pytest.global_dai = Wad(0)


class TestDsrManager:

    def test_getters(self, mcd: DssDeployment):
        assert isinstance(mcd.dsr_manager.pot(), Pot)
        assert mcd.dsr_manager.pot().address.address == mcd.pot.address.address
        assert isinstance(mcd.dsr_manager.dai(), DSToken)
        assert mcd.dsr_manager.dai().address.address == mcd.dai.address.address
        assert isinstance(mcd.dsr_manager.dai_adapter(), DaiJoin)
        assert mcd.dsr_manager.dai_adapter().address.address == mcd.dai_adapter.address.address

    def test_join(self, mcd: DssDeployment, our_address: Address):

        # Mint 58 Dai and lock it in the Pot contract through DsrManager
        more_dai = Wad.from_number(58)
        mint_dai(mcd=mcd, amount=more_dai, ilkName='ETH-A', our_address=our_address)
        dai = mcd.dai.balance_of(our_address)
        assert mcd.dai.approve(mcd.dsr_manager.address).transact(from_address=our_address)
        assert mcd.dsr_manager.supply() == Wad(0)

        # Join through DsrManager an ensure Dai Token balance is depleted
        assert mcd.dsr_manager.join(our_address, dai).transact(from_address=our_address)
        assert mcd.dai.balance_of(our_address) == Wad(0)

        pytest.global_dai = dai

    def test_supply_pie_dai(self, mcd: DssDeployment, our_address: Address):

        dai = pytest.global_dai
        chi1 = mcd.pot.chi()
        # assert chi1 == Ray.from_number(1) Commented out in case there's some initial state on testchain
        pie = Wad(Rad(dai) / Rad(chi1))
        assert mcd.dsr_manager.supply() == pie
        assert mcd.dsr_manager.pie_of(our_address) == pie

        time_travel_by(web3=mcd.web3, seconds=10)
        assert mcd.pot.drip().transact(from_address=our_address)
        chi2 = mcd.pot.chi()
        assert chi1 != chi2
        dai = Rad(pie) * Rad(chi2)
        assert mcd.dsr_manager.dai_of(our_address) == dai

    def test_exit(self, mcd: DssDeployment, our_address: Address):

        dai = pytest.global_dai
        assert mcd.dai.balance_of(our_address) == Wad.from_number(0)
        # since drip was called in previous test, there should be some amount left
        assert mcd.dsr_manager.exit(our_address, dai).transact(from_address=our_address)

        assert mcd.dai.balance_of(our_address) == dai
        assert mcd.dsr_manager.supply() != Wad(0)

        assert mcd.dsr_manager.exitAll(our_address).transact(from_address=our_address)
        assert mcd.dai.balance_of(our_address) > dai
        assert mcd.dsr_manager.supply() == Wad(0)
