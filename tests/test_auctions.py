# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2018 reverendus, bargst
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
from web3 import HTTPProvider
from web3 import Web3

from pymaker import Address, Wad
from pymaker.auctions import Flipper, Flapper, Flopper
from pymaker.auth import DSGuard
from pymaker.deployment import DssDeployment
from pymaker.numeric import Ray
from pymaker.token import DSToken


class TestFlipper:
    @pytest.fixture(scope="session")
    def flipper(self, mcd: DssDeployment) -> Flipper:
        # TODO: Call file methods to reduce ttl and tau to testable durations
        return mcd.collaterals[0].flipper

    def test_getters(self, mcd, flipper):
        # FIXME: Seems like auction points to DaiMove/GemMove contracts
        # assert flipper.dai() == mcd.dai.address
        # assert flipper.gem() == mcd.collaterals[0].gem.address
        assert flipper.beg() == Ray.from_number(1.05)
        assert flipper.ttl() == 3 * 60 * 60  # 3 hours
        assert flipper.tau() == 2 * 24 * 60 * 60  # 2 days
        assert flipper.kicks() >= 0

    def test_scenario(self, mcd, flipper, our_address, other_address):
        self.kick(mcd, flipper, our_address, other_address)

        # TODO: Set quantities relative to auction parameters
        flipper.tend(1, Wad.from_number(100), Wad.from_number(2000)).transact()
        flipper.tend(1, Wad.from_number(100), Wad.from_number(5000)).transact()
        flipper.dent(1, Wad.from_number(80), Wad.from_number(5000)).transact()

        # TODO: Wait for auction to end
        flipper.deal(1).transact()

    def kick(self, flipper, our_address, other_address):
        assert self.flapper.kicks() == 0
        assert flipper.kick(urn=our_address,
                            gal=other_address,
                            tab=Wad.from_number(5000),
                            lot=Wad.from_number(100),
                            bid=Wad.from_number(100)).transact()
        assert flipper.kicks() == 1

        # Ensure a default bid is created
        auction = self.flipper.bids(1)
        assert auction.lad == our_address
        assert auction.gal == other_address
        assert auction.bid == Wad.from_number(100)
        assert auction.lot == Wad.from_number(100)
        assert auction.tab == Wad.from_number(5000)
        assert auction.guy == our_address
        assert auction.tic == 0
        assert auction.end > 0


class TestFlapper:
    @pytest.fixture(scope="session")
    def flapper(self, mcd: DssDeployment) -> Flapper:
        # TODO: Call file methods to reduce ttl and tau to testable durations
        return mcd.flap

    def test_getters(self, mcd, flapper):
        # FIXME: Seems like auction points to DaiMove/GemMove contracts
        # assert flapper.dai() == mcd.dai.address
        # assert flapper.gem() == mcd.collaterals[0].gem.address
        assert flapper.beg() == Ray.from_number(1.05)
        assert flapper.ttl() == 3 * 60 * 60
        assert flapper.tau() == 2 * 24 * 60 * 60
        assert flapper.kicks() >= 0

    def test_scenario(self, flapper, our_address, other_address):
        assert flapper.kicks() == 0
        flapper.kick(our_address, Wad.from_number(20000), Wad.from_number(1)).transact()
        assert flapper.kicks() == 1

        auction = self.flapper.bids(1)
        assert auction.bid == Wad.from_number(1)
        assert auction.lot == Wad.from_number(20000)
        assert auction.guy == self.our_address
        assert auction.tic == 0
        assert auction.end > 0

        # TODO: Set quantities relative to auction parameters
        flapper.tend(1, Wad.from_number(20000), Wad.from_number(1.5)).transact()
        assert flapper.bids(1).tic > 0
        flapper.tend(1, Wad.from_number(20000), Wad.from_number(2.0)).transact()
        assert flapper.bids(1).tic > 0

        # TODO: Wait for auction to end
        flapper.deal(1).transact()


class TestFlopper:
    @pytest.fixture(scope="session")
    def flopper(self, mcd: DssDeployment) -> Flopper:
        # TODO: Call file methods to reduce ttl and tau to testable durations
        return mcd.flop

    def test_getters(self, mcd, flopper):
        # FIXME: Seems like auction points to DaiMove/GemMove contracts
        # assert flopper.dai() == mcd.dai.address
        # assert flopper.gem() == mcd.collaterals[0].gem.address
        assert flopper.beg() == Ray.from_number(1.05)
        assert flopper.ttl() == 3*60*60
        assert flopper.tau() == 2*24*60*60
        assert flopper.kicks() >= 0

    def test_scenario(self, flopper, our_address, other_address):
        assert flopper.kicks() == 0
        flopper.kick(our_address, Wad.from_number(10), Wad.from_number(20000)).transact()
        assert flopper.kicks() == 1

        auction = flopper.bids(1)
        assert auction.bid == Wad.from_number(20000)
        assert auction.lot == Wad.from_number(10)
        assert auction.guy == our_address
        assert auction.tic == 0
        assert auction.end > 0

        # TODO: Set quantities relative to auction parameters
        flopper.dent(1, Wad.from_number(9), Wad.from_number(20000)).transact()
        assert flopper.bids(1).tic > 0
        flopper.dent(1, Wad.from_number(8), Wad.from_number(20000)).transact()
        assert flopper.bids(1).tic > 0

        # TODO: Wait for auction to end
        self.flopper.deal(1).transact()

