# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 grandizzy
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
from pymaker.deployment import DssDeployment
from pymaker.dsr import Dsr
from pymaker.numeric import Wad

from tests.test_dss import wrap_eth, frob, max_dart


@pytest.fixture
def dsr(our_address: Address, mcd: DssDeployment) -> Dsr:
    return Dsr(mcd, our_address)


@pytest.mark.dependency()
def test_proxy(dsr):
    assert dsr.has_proxy() is False

    dsr.build_proxy().transact()
    assert dsr.has_proxy() is True


@pytest.mark.dependency(depends=['test_proxy'])
def test_join_and_exit(dsr):
    proxy = dsr.get_proxy()
    assert dsr.get_balance(proxy.address) == Wad.from_number(0)

    mcd = dsr.mcd

    # Create a CDP
    collateral = mcd.collaterals['ETH-A']
    wrap_eth(mcd, dsr.owner, Wad.from_number(1))
    collateral.approve(dsr.owner)
    assert collateral.adapter.join(dsr.owner, Wad.from_number(1)).transact(from_address=dsr.owner)
    frob(mcd, collateral, dsr.owner, dink=Wad.from_number(1), dart=Wad(0))
    dart = max_dart(mcd, collateral, dsr.owner) - Wad(1)
    frob(mcd, collateral, dsr.owner, dink=Wad(0), dart=dart)

    # Mint and withdraw all the Dai
    mcd.approve_dai(dsr.owner)
    assert mcd.dai_adapter.exit(dsr.owner, dart).transact(from_address=dsr.owner)
    assert mcd.dai.balance_of(dsr.owner) == dart

    intial_dai_balance = mcd.dai.balance_of(dsr.owner)
    assert intial_dai_balance > Wad.from_number(0)
    assert dsr.get_balance(proxy.address) == Wad.from_number(0)

    # approve Proxy to use 100 DAI from account
    mcd.dai.approve(proxy.address, Wad.from_number(100)).transact(from_address=dsr.owner)

    # join 100 DAI in DSR
    dsr.join(Wad.from_number(100), proxy).transact(from_address=dsr.owner)
    assert mcd.dai.balance_of(dsr.owner) == intial_dai_balance - Wad.from_number(100)
    assert round(dsr.get_balance(proxy.address)) == Wad.from_number(100)

    # exit 33 DAI from DSR
    dsr.exit(Wad.from_number(33), proxy).transact(from_address=dsr.owner)
    assert round(mcd.dai.balance_of(dsr.owner)) == round(intial_dai_balance) - Wad.from_number(100) + Wad.from_number(33)
    assert round(dsr.get_balance(proxy.address)) == Wad.from_number(67)

    # exit remaining DAI from DSR
    dsr.exit_all(proxy).transact(from_address=dsr.owner)
    assert round(mcd.dai.balance_of(dsr.owner)) == round(intial_dai_balance)
    assert dsr.get_balance(proxy.address) == Wad.from_number(0)
