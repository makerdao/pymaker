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
import time
from datetime import datetime
from web3 import Web3

from pymaker.approval import hope_directly
from pymaker.auctions import Flipper, Flapper, Flopper
from pymaker.deployment import DssDeployment
from pymaker.dss import Collateral, Urn
from pymaker.numeric import Wad, Ray, Rad
from tests.test_dss import TestVat, TestCat, wrap_eth, set_collateral_price


class TestFlipper:
    @pytest.fixture(scope="session")
    def collateral(self, mcd: DssDeployment) -> Collateral:
        return mcd.collaterals[0]

    @pytest.fixture(scope="session")
    def flipper(self, collateral, deployment_address) -> Flipper:
        # Reduce ttl and tau to testable durations
        flipper = collateral.flipper
        # FIXME: We don't have permission to change bid/auction duration
        # assert flipper.wards(deployment_address)
        # assert flipper.file_ttl(2).transact(from_address=deployment_address)     # Bids expire in 2 seconds
        # assert flipper.file_tau(10).transact(from_address=deployment_address)    # Auction expires in 10 seconds
        # assert flipper.ttl() == 2
        # assert flipper.tau == 10
        return flipper

    def test_getters(self, mcd, flipper):
        assert flipper.beg() == Ray.from_number(1.05)
        assert flipper.ttl() == 3 * 60 * 60  # 3 hours
        assert flipper.tau() == 2 * 24 * 60 * 60  # 2 days
        assert flipper.kicks() >= 0

    def test_scenario(self, web3, mcd, collateral, flipper, our_address, other_address, deployment_address):
        # Create a CDP
        collateral = mcd.collaterals[0]
        kicks_before = flipper.kicks()
        ilk = collateral.ilk
        wrap_eth(mcd, deployment_address, Wad.from_number(1))
        assert collateral.adapter.join(Urn(deployment_address), Wad.from_number(1)).transact(
            from_address=deployment_address)
        TestVat.frob(mcd, collateral, deployment_address, dink=Wad.from_number(1), dart=Wad(0))
        max_dart = TestVat.max_dart(mcd, collateral, deployment_address) - Wad(1)
        TestVat.frob(mcd, collateral, deployment_address, dink=Wad(0), dart=max_dart)

        # Mint and withdraw all the Dai
        # FIXME: need a way to pass from_address to the approval function
        web3.eth.defaultAccount = deployment_address.address
        mcd.dai_adapter.approve(approval_function=hope_directly(), vat=mcd.vat.address)
        assert mcd.dai_adapter.exit(Urn(deployment_address), max_dart).transact(from_address=deployment_address)
        assert mcd.dai.balance_of(deployment_address) == max_dart
        assert mcd.vat.dai(deployment_address) == Rad(0)

        # Undercollateralize the CDP
        to_price = Wad(Web3.toInt(collateral.pip.read())) / Wad.from_number(2)
        set_collateral_price(mcd, collateral, to_price)
        urn = mcd.vat.urn(collateral.ilk, deployment_address)
        ilk = mcd.vat.ilk(ilk.name)
        assert ilk.rate is not None
        assert ilk.spot is not None
        safe = Ray(urn.art) * mcd.vat.ilk(ilk.name).rate <= Ray(urn.ink) * ilk.spot
        assert not safe

        # Bite the CDP, which moves debt to the vow and kicks the flipper
        urn = mcd.vat.urn(collateral.ilk, deployment_address)
        assert urn.ink > Wad(0)
        lot = min(urn.ink, mcd.cat.lump(ilk))  # Wad
        art = min(urn.art, (lot * urn.art) / urn.ink)  # Wad
        tab = art * ilk.rate * Wad(mcd.cat.chop(ilk))  # Wad
        assert tab == max_dart
        TestCat.simulate_bite(mcd, collateral, deployment_address)
        assert mcd.cat.bite(collateral.ilk, Urn(deployment_address)).transact()
        urn = mcd.vat.urn(collateral.ilk, deployment_address)
        # Check vat, vow, and cat
        assert urn.ink == Wad(0)
        assert urn.art == max_dart - art
        assert mcd.vat.vice() > Rad(0)
        assert mcd.vow.sin() == Rad(tab)
        bites = mcd.cat.past_bite(10)
        assert len(bites) == 1
        last_bite = bites[0]
        assert last_bite.tab > Rad(0)
        print(f"last_bite={last_bite}")
        # Check the flipper
        assert flipper.kicks() == kicks_before + 1
        current_bid = flipper.bids(1)
        print(f"initial bid={current_bid}")
        assert isinstance(current_bid, Flipper.Bid)
        assert current_bid.lot > Wad(0)
        assert current_bid.tab > Rad(0)
        assert current_bid.bid == Rad(0)
        assert last_bite.tab == current_bid.tab

        # Test the _tend_ phase of the auction
        eth_required = Wad(current_bid.tab / Rad(ilk.spot)) * Wad.from_number(1.1)
        wrap_eth(mcd, other_address, eth_required)
        assert collateral.gem.balance_of(other_address) >= eth_required
        collateral.gem.approve(collateral.adapter.address)
        other_urn = mcd.vat.urn(collateral.ilk, other_address)
        assert collateral.adapter.join(other_urn, eth_required).transact(from_address=other_address)
        # FIXME: need a way to pass from_address to the approval function
        web3.eth.defaultAccount = other_address.address
        flipper.approve(approval_function=hope_directly())
        assert mcd.vat.can(other_address, flipper.address)
        TestVat.frob(mcd, collateral, other_address, dink=eth_required, dart=Wad(current_bid.tab))
        # Bid the tab to instantly transition to dent stage
        assert flipper.tend(1, current_bid.lot, current_bid.tab).transact(from_address=other_address)
        current_bid = flipper.bids(1)
        assert current_bid.guy == other_address
        assert current_bid.bid == current_bid.tab

        # Test the _dent_ phase of the auction
        wrap_eth(mcd, our_address, eth_required)
        our_urn = mcd.vat.urn(collateral.ilk, our_address)
        assert collateral.adapter.join(our_urn, eth_required).transact(from_address=our_address)
        web3.eth.defaultAccount = our_address.address
        flipper.approve(approval_function=hope_directly())
        TestVat.frob(mcd, collateral, our_address, dink=eth_required, dart=Wad(current_bid.tab))
        lot = current_bid.lot - Wad.from_number(0.2)
        assert flipper.beg() * Ray(lot) <= Ray(current_bid.lot)
        assert current_bid.tic > datetime.now().timestamp() or current_bid.tic == 0
        assert current_bid.end > datetime.now().timestamp()
        assert mcd.vat.can(our_address, flipper.address)
        assert flipper.dent(1, lot, current_bid.tab).transact(from_address=our_address)
        current_bid = flipper.bids(1)
        assert current_bid.guy == our_address
        assert current_bid.bid == current_bid.tab
        assert current_bid.lot == lot

        # TODO: Exercise _deal_ after a testable bid duration has been configured
        # time.sleep(3)
        # assert flipper.deal(1).transact(from_address=our_address)
        # print(f"bids after deal: {flipper.bids(1)}")


class TestFlapper:
    @pytest.fixture(scope="session")
    def flapper(self, mcd: DssDeployment) -> Flapper:
        # Call file methods to produce testable durations
        mcd.flap.file_beg(Ray.from_number(1.04))  # 4% bid increment
        mcd.flap.file_ttl(2)   # 2 second bids
        mcd.flap.file_tau(15)  # 15 second auctions
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

        # TODO: Test removal of bid
        flapper.yank(1).transact()

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
        # TODO: If the flip auction didn't cover the debt, kick the flopper
        # awe = vat.sin
        # woe = (awe-sin)-ash
        # assert mcd.vow.woe() >= mcd.vow.sump()
        # assert mcd.vow.joy() == Wad(0)
        # assert mcd.vow.flop().transact()

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



