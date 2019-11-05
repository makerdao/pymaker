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


import pytest
from datetime import datetime, timedelta

from pymaker import Address
from pymaker.approval import directly, hope_directly
from pymaker.deployment import DssDeployment
from pymaker.dss import Collateral
from pymaker.numeric import Wad, Ray, Rad
from pymaker.shutdown import ShutdownModule, End

from tests.test_auctions import create_surplus
from tests.test_dss import mint_mkr, wrap_eth, frob


def open_cdp(mcd: DssDeployment, collateral: Collateral, address: Address):
    assert isinstance(mcd, DssDeployment)
    assert isinstance(collateral, Collateral)
    assert isinstance(address, Address)

    collateral.approve(address)
    wrap_eth(mcd, address, Wad.from_number(10))
    assert collateral.adapter.join(address, Wad.from_number(10)).transact(from_address=address)
    frob(mcd, collateral, address, Wad.from_number(10), Wad.from_number(15))

    assert mcd.vat.debt() >= Rad(Wad.from_number(15))
    assert mcd.vat.dai(address) >= Rad.from_number(10)


def create_flap_auction(mcd: DssDeployment, deployment_address: Address, our_address: Address):
    assert isinstance(mcd, DssDeployment)
    assert isinstance(deployment_address, Address)
    assert isinstance(our_address, Address)

    flapper = mcd.flapper
    create_surplus(mcd, flapper, deployment_address)
    joy = mcd.vat.dai(mcd.vow.address)
    assert joy > mcd.vat.sin(mcd.vow.address) + mcd.vow.bump() + mcd.vow.hump()
    assert (mcd.vat.sin(mcd.vow.address) - mcd.vow.sin()) - mcd.vow.ash() == Rad(0)
    assert mcd.vow.flap().transact()

    mint_mkr(mcd.mkr, our_address, Wad.from_number(10))
    flapper.approve(mcd.mkr.address, directly(from_address=our_address))
    bid = Wad.from_number(0.001)
    assert mcd.mkr.balance_of(our_address) > bid
    assert flapper.tend(flapper.kicks(), mcd.vow.bump(), bid).transact(from_address=our_address)


nobody = Address("0x0000000000000000000000000000000000000000")


class TestShutdownModule:
    """This test must be run after other MCD tests because it will leave the testchain `cage`d."""

    def test_init(self, mcd, deployment_address, our_address):
        assert mcd.esm is not None
        assert isinstance(mcd.esm, ShutdownModule)
        assert isinstance(mcd.esm.address, Address)
        assert mcd.esm.sum() == Wad(0)
        assert mcd.esm.min() > Wad(0)
        assert not mcd.esm.fired()

        joy = mcd.vat.dai(mcd.vow.address)
        awe = mcd.vat.sin(mcd.vow.address)
        # If `test_shutdown.py` is run in isolation, create a flap auction to exercise `yank`
        if joy == Rad(0) and awe == Rad(0):
            create_flap_auction(mcd, deployment_address, our_address)

    def test_join(self, mcd, our_address):
        assert mcd.mkr.approve(mcd.esm.address).transact()

        # This should have no effect yet succeed regardless
        assert mcd.esm.join(Wad(0)).transact()
        assert mcd.esm.sum() == Wad(0)
        assert mcd.esm.sum_of(our_address) == Wad(0)

        # Ensure the appropriate amount of MKR can be joined
        mint_mkr(mcd.mkr, our_address, mcd.esm.min())
        assert mcd.esm.join(mcd.esm.min()).transact()
        assert mcd.esm.sum() == mcd.esm.min()

        # Joining extra MKR should succeed yet have no effect
        mint_mkr(mcd.mkr, our_address, Wad(153))
        assert mcd.esm.join(Wad(153)).transact()
        assert mcd.esm.sum() == mcd.esm.min() + Wad(153)
        assert mcd.esm.sum_of(our_address) == mcd.esm.sum()

    def test_fire(self, mcd, our_address):
        open_cdp(mcd, mcd.collaterals['ETH-A'], our_address)

        assert mcd.end.live()
        assert mcd.esm.fire().transact()
        assert mcd.esm.fired()
        assert not mcd.end.live()


class TestEnd:
    """This test must be run after TestShutdownModule, which calls `esm.fire`."""

    def test_init(self, mcd):
        assert mcd.end is not None
        assert isinstance(mcd.end, End)
        assert isinstance(mcd.esm.address, Address)

    def test_getters(self, mcd):
        assert not mcd.end.live()
        assert datetime.utcnow() - timedelta(minutes=5) < mcd.end.when() < datetime.utcnow()
        assert mcd.end.wait() >= 0
        assert mcd.end.debt() >= Rad(0)

        for collateral in mcd.collaterals.values():
            ilk = collateral.ilk
            assert mcd.end.tag(ilk) == Ray(0)
            assert mcd.end.gap(ilk) == Wad(0)
            assert mcd.end.art(ilk) == Wad(0)
            assert mcd.end.fix(ilk) == Ray(0)

    def test_cage(self, mcd):
        collateral = mcd.collaterals['ETH-A']
        ilk = collateral.ilk

        assert mcd.end.cage(ilk).transact()
        assert mcd.end.art(ilk) > Wad(0)
        assert mcd.end.tag(ilk) > Ray(0)

    def test_yank(self, mcd):
        last_flap = mcd.flapper.bids(mcd.flapper.kicks())
        last_flop = mcd.flopper.bids(mcd.flopper.kicks())
        if last_flap.end > 0 and last_flap.guy is not nobody:
            auction = mcd.flapper
        elif last_flop.end > 0 and last_flop.guy is not nobody:
            auction = mcd.flopper
        else:
            auction = None

        if auction:
            print(f"active {auction} auction: {auction.bids(auction.kicks())}")
            assert not auction.live()
            kick = auction.kicks()
            assert auction.yank(kick).transact()
            assert auction.bids(kick).guy == nobody

    def test_skim(self, mcd, our_address):
        ilk = mcd.collaterals['ETH-A'].ilk

        urn = mcd.vat.urn(ilk, our_address)
        owe = Ray(urn.art) * mcd.vat.ilk(ilk.name).rate * mcd.end.tag(ilk)
        assert owe > Ray(0)
        wad = min(Ray(urn.ink), owe)
        print(f"owe={owe} wad={wad}")

        assert mcd.end.skim(ilk, our_address).transact()
        assert mcd.vat.urn(ilk, our_address).art == Wad(0)
        assert mcd.vat.urn(ilk, our_address).ink > Wad(0)
        assert mcd.vat.sin(mcd.vow.address) > Rad(0)

        assert mcd.vat.debt() > Rad(0)
        assert mcd.vat.vice() > Rad(0)

    @pytest.mark.skip(reason="unable to determine redemption price")
    def test_close_cdp(self, mcd, our_address):
        collateral = mcd.collaterals['ETH-A']
        ilk = collateral.ilk

        assert mcd.end.free(ilk).transact()
        assert mcd.vat.urn(ilk, our_address).ink == Wad(0)
        assert mcd.vat.gem(ilk, our_address) > Wad(0)
        assert collateral.adapter.exit(our_address, mcd.vat.gem(ilk, our_address)).transact()

        assert mcd.end.wait() == 0
        assert mcd.end.thaw().transact()
        assert mcd.end.flow(ilk).transact()
        # FIXME: `flow` should determine redemption price for the collateral
        assert mcd.end.fix(ilk) > Ray(0)

    @pytest.mark.skip(reason="unable to add dai to the `bag`")
    def test_pack(self, mcd, our_address):
        assert mcd.end.bag(our_address) == Wad(0)
        assert mcd.end.debt() > Rad(0)
        assert mcd.dai.approve(mcd.end.address).transact()
        assert mcd.vat.dai(our_address) >= Rad.from_number(10)
        # FIXME: `pack` fails, possibly because we're passing 0 to `vat.flux`
        assert mcd.end.pack(Wad.from_number(10)).transact()
        assert mcd.end.bag(our_address) == Wad.from_number(10)
