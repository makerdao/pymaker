# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2018 bargst
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
from web3 import Web3, HTTPProvider

from tests.helpers import time_travel_by, snapshot, reset

from pymaker import Address
from pymaker.auctions import Flipper
from pymaker.deployment import DssDeployment
from pymaker.dss import Cat, Ilk, Urn
from pymaker.numeric import Ray, Wad, Rad


@pytest.fixture(scope="session")
def web3():
    web3 = Web3(HTTPProvider("http://localhost:8555"))
    web3.eth.defaultAccount = web3.eth.accounts[0]
    return web3


@pytest.fixture(scope="session")
def other_address(web3):
    return Address(web3.eth.accounts[1])


@pytest.fixture(scope="session")
def our_address(web3):
    return Address(web3.eth.accounts[0])


@pytest.fixture(scope="session")
def d(web3):
    deployment = DssDeployment.deploy(web3=web3, debt_ceiling=Wad.from_number(1000000))
    for c in deployment.collaterals:
        assert c.gem.mint(Wad.from_number(1000)).transact()
    return deployment


@pytest.fixture()
def bite_event(our_address: Address, d: DssDeployment):
    collateral = d.collaterals[0]

    # Add collateral to our CDP
    assert collateral.adapter.join(Urn(our_address), Wad.from_number(1)).transact()
    assert d.pit.frob(collateral.ilk, Wad.from_number(1), Wad(0)).transact()

    # Define required bite parameters
    our_urn = d.vat.urn(collateral.ilk, our_address)
    max_dart = our_urn.ink * d.pit.spot(collateral.ilk) - our_urn.art
    to_price = Wad(Web3.toInt(collateral.pip.read())) - Wad.from_number(1)

    # Manipulate price to make our CDP underwater
    assert d.pit.frob(collateral.ilk, Wad(0), max_dart).transact()
    assert collateral.pip.poke_with_int(to_price.value).transact()
    assert collateral.spotter.poke().transact()

    # Bite the CDP
    assert d.cat.bite(collateral.ilk, Urn(our_address)).transact()

    # Return the corresponding event
    return d.cat.past_bite(1)[0]


class TestVat:
    """ `Vat` class testing"""

    def test_rely(self, d: DssDeployment, other_address: Address):
        # when
        assert d.vat.rely(other_address).transact()

        # then
        assert d.vat.init(Ilk('ETH')).transact(from_address=other_address)

    def test_ilk(self, d: DssDeployment):
        assert d.vat.ilk('XXX') == Ilk('XXX', take=Ray(0), rate=Ray(0), ink=Wad(0), art=Wad(0))

    def test_gem(self, our_address: Address, d: DssDeployment):
        collateral = d.collaterals[0]

        # when
        assert collateral.adapter.join(Urn(our_address), Wad(10)).transact()

        # then
        assert d.vat.gem(collateral.ilk, our_address) == Rad(Wad(10))


class TestPit:
    def test_frob_noop(self, d: DssDeployment, our_address: Address):
        # given
        collateral = d.collaterals[0]
        our_urn = d.vat.urn(collateral.ilk, our_address)

        # when
        assert d.pit.frob(collateral.ilk, Wad(0), Wad(0)).transact()

        # then
        assert d.vat.urn(collateral.ilk, our_address) == our_urn

    def test_frob_add_ink(self, d: DssDeployment, our_address: Address):
        # given
        collateral = d.collaterals[0]
        our_urn = d.vat.urn(collateral.ilk, our_address)

        # when
        assert collateral.adapter.join(our_urn, Wad(10)).transact()
        assert d.pit.frob(collateral.ilk, Wad(10), Wad(0)).transact()

        # then
        assert d.vat.urn(collateral.ilk, our_address).ink == our_urn.ink + Wad(10)

    def test_frob_add_art(self, d: DssDeployment, our_address: Address):
        # given
        collateral = d.collaterals[0]
        our_urn = d.vat.urn(collateral.ilk, our_address)

        # when
        assert collateral.adapter.join(our_urn, Wad.from_number(10)).transact()
        assert d.pit.frob(collateral.ilk, Wad(0), Wad(10)).transact()

        # then
        assert d.vat.urn(collateral.ilk, our_address).art == our_urn.art + Wad(10)

    def test_past_frob(self, our_address, d: DssDeployment):
        # given
        c = d.collaterals[0]

        # when
        assert d.pit.frob(c.ilk, Wad(0), Wad(0)).transact()

        # then
        last_frob_event = d.pit.past_frob(1, event_filter={'ilk': c.ilk.toBytes()})[-1]
        assert last_frob_event.ilk == c.ilk
        assert last_frob_event.dink == Wad(0)
        assert last_frob_event.dart == Wad(0)
        assert last_frob_event.urn.address == our_address


class TestCat:
    def test_empty_flips(self, d: DssDeployment):
        nflip = d.cat.nflip()
        assert d.cat.flips(nflip + 1) == Cat.Flip(nflip + 1,
                                                  Urn(Address('0x0000000000000000000000000000000000000000')),
                                                  Wad(0))

    def test_bite(self, our_address, d: DssDeployment):
        # given
        collateral = d.collaterals[0]
        assert collateral.adapter.join(Urn(our_address), Wad.from_number(2)).transact()
        assert d.pit.frob(collateral.ilk, Wad.from_number(2), Wad(0)).transact()
        our_urn = d.vat.urn(collateral.ilk, our_address)
        max_dart = our_urn.ink * d.pit.spot(collateral.ilk) - our_urn.art
        to_price = Wad(Web3.toInt(collateral.pip.read())) - Wad.from_number(10)

        # when
        assert d.pit.frob(collateral.ilk, Wad(0), max_dart).transact()
        assert collateral.pip.poke_with_int(to_price.value).transact()
        assert collateral.spotter.poke().transact()

        # then
        assert d.cat.bite(collateral.ilk, Urn(our_address)).transact()

    def test_past_bite(self, d: DssDeployment, bite_event):
        assert d.cat.past_bite(1) == [bite_event]

    def test_flip(self, web3, d: DssDeployment, bite_event):
        # given
        nflip = d.cat.nflip()
        flipper = Flipper(web3=web3, address=d.cat.flipper(bite_event.ilk))
        kicks = flipper.kicks()

        # when
        assert nflip > 0
        flip = d.cat.flips(nflip - 1)
        assert flip.tab > Wad(0)
        lump = d.cat.lump(flip.urn.ilk)
        if flip.tab < lump:
            assert d.cat.flip(flip, flip.tab).transact()
        else:
            assert d.cat.flip(flip, lump).transact()

        # then
        assert flipper.kicks() == kicks + 1
        assert d.cat.flips(flip.id).tab == Wad(0)


class TestVow:
    def test_getters(self, d: DssDeployment):
        assert isinstance(d.vow.flopper(), Address)
        assert isinstance(d.vow.flopper(), Address)
        assert isinstance(d.vow.sin(), Wad)
        assert isinstance(d.vow.sin_of(0), Wad)
        assert isinstance(d.vow.woe(), Wad)
        assert isinstance(d.vow.ash(), Wad)
        assert isinstance(d.vow.joy(), Wad)
        assert isinstance(d.vow.awe(), Wad)
        assert isinstance(d.vow.wait(), int)
        assert isinstance(d.vow.sump(), Wad)
        assert isinstance(d.vow.bump(), Wad)
        assert isinstance(d.vow.hump(), Wad)

    def test_empty_flog(self, web3, d: DssDeployment):
        time_travel_by(web3, d.vow.wait() + 10)
        assert d.vow.flog(0).transact()

    def test_flog(self, web3, d: DssDeployment, bite_event):
        # given
        time_travel_by(web3, d.vow.wait() + 10)
        era = web3.eth.getBlock(bite_event.raw['blockNumber'])['timestamp']
        assert d.vow.sin_of(era) != Wad(0)

        # when
        assert d.vow.flog(era).transact()

        # then
        assert d.vow.sin_of(era) == Wad(0)

    def test_heal(self, d: DssDeployment):
        assert d.vow.heal(Wad(0)).transact()

    def test_kiss(self, d: DssDeployment):
        assert d.vow.kiss(Wad(0)).transact()

    def test_flap(self, web3, our_address, d: DssDeployment):
        # given
        snap_id = snapshot(web3)
        c = d.collaterals[0]
        assert c.adapter.join(Urn(our_address), Wad.from_number(200)).transact()
        assert d.pit.frob(c.ilk, Wad.from_number(200), Wad.from_number(11000)).transact()
        assert d.dai_move.move(our_address, d.vow.address, Wad.from_number(11000)).transact()

        # when
        assert d.vow.heal(d.vow.woe()).transact()
        assert d.vow.joy() >= (d.vow.awe() + d.vow.bump() + d.vow.hump())
        assert d.vow.woe() == Wad(0)

        # then
        assert d.vow.flap().transact()

        # cleanup
        reset(web3, snap_id)

    def test_flop(self, web3, d: DssDeployment, bite_event):
        # given
        print(d)
        for be in d.cat.past_bite(100000):
            if be.tab > Wad(0):
                era = be.era(web3)
                assert d.vow.flog(era).transact()

        # when
        assert d.vow.woe() >= d.vow.sump()
        assert d.vow.joy() == Wad(0)

        # then
        assert d.vow.flop().transact()


class TestDrip:
    def test_getters(self, d: DssDeployment):
        c = d.collaterals[0]
        assert isinstance(d.drip.vow(), Urn)
        assert isinstance(d.drip.vat(), Address)
        assert isinstance(d.drip.repo(), Wad)
        assert isinstance(d.drip.tax(c.ilk), Ray)
        assert isinstance(d.drip.rho(c.ilk), int)

    def test_drip(self, d: DssDeployment):
        # given
        c = d.collaterals[0]

        # then
        assert d.drip.drip(c.ilk).transact()

    def test_file_tax(self, d: DssDeployment):
        # given
        c = d.collaterals[0]

        # then
        assert d.drip.file_tax(c.ilk, Ray(1000000564701133626865910626)).transact()
