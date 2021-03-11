# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2018-2019 reverendus, bargst, EdNoepel
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
from datetime import datetime
from web3 import Web3

from pymaker import Address
from pymaker.approval import directly, hope_directly
from pymaker.auctions import DealableAuctionContract, Clipper, Flapper, Flipper, Flopper
from pymaker.deployment import Collateral, DssDeployment
from pymaker.numeric import Wad, Ray, Rad
from tests.helpers import time_travel_by
from tests.test_dss import wrap_eth, mint_mkr, set_collateral_price, wait, frob, cleanup_urn, max_dart


def create_surplus(mcd: DssDeployment, flapper: Flapper, deployment_address: Address):
    assert isinstance(mcd, DssDeployment)
    assert isinstance(flapper, Flapper)
    assert isinstance(deployment_address, Address)

    joy = mcd.vat.dai(mcd.vow.address)

    if joy < mcd.vat.sin(mcd.vow.address) + mcd.vow.hump() + mcd.vow.bump():
        # Create a CDP with surplus
        print('Creating a CDP with surplus')
        collateral = mcd.collaterals['ETH-B']
        assert flapper.kicks() == 0
        wrap_eth(mcd, deployment_address, Wad.from_number(100))
        collateral.approve(deployment_address)
        assert collateral.adapter.join(deployment_address, Wad.from_number(100)).transact(
            from_address=deployment_address)
        frob(mcd, collateral, deployment_address, dink=Wad.from_number(100), dart=Wad.from_number(1000))
        assert mcd.jug.drip(collateral.ilk).transact(from_address=deployment_address)
        joy = mcd.vat.dai(mcd.vow.address)
        assert joy >= mcd.vow.hump() + mcd.vow.bump()
    else:
        print(f'Surplus of {joy} already exists; skipping CDP creation')


def create_debt(web3: Web3, mcd: DssDeployment, our_address: Address, deployment_address: Address):
    assert isinstance(web3, Web3)
    assert isinstance(mcd, DssDeployment)
    assert isinstance(our_address, Address)
    assert isinstance(deployment_address, Address)

    # Create a vault
    collateral = mcd.collaterals['ETH-A']
    ilk = collateral.ilk
    wrap_eth(mcd, deployment_address, Wad.from_number(1))
    collateral.approve(deployment_address)
    assert collateral.adapter.join(deployment_address, Wad.from_number(1)).transact(
        from_address=deployment_address)
    frob(mcd, collateral, deployment_address, dink=Wad.from_number(1), dart=Wad(0))
    dart = max_dart(mcd, collateral, deployment_address) - Wad(1)
    frob(mcd, collateral, deployment_address, dink=Wad(0), dart=dart)
    assert not mcd.cat.can_bite(ilk, mcd.vat.urn(collateral.ilk, deployment_address))

    # Undercollateralize by dropping the spot price, and then bite the vault
    to_price = Wad(Web3.toInt(collateral.pip.read())) / Wad.from_number(2)
    set_collateral_price(mcd, collateral, to_price)
    urn = mcd.vat.urn(collateral.ilk, deployment_address)
    assert urn.ink is not None and urn.art is not None
    assert ilk.spot is not None
    safe = Ray(urn.art) * mcd.vat.ilk(ilk.name).rate <= Ray(urn.ink) * ilk.spot
    assert not safe
    assert mcd.cat.can_bite(collateral.ilk, urn)
    assert mcd.cat.bite(collateral.ilk, urn).transact()
    flip_kick = collateral.flipper.kicks()

    # Generate some Dai, bid on and win the flip auction without covering all the debt
    wrap_eth(mcd, our_address, Wad.from_number(10))
    collateral.approve(our_address)
    assert collateral.adapter.join(our_address, Wad.from_number(10)).transact(from_address=our_address)
    web3.eth.defaultAccount = our_address.address
    frob(mcd, collateral, our_address, dink=Wad.from_number(10), dart=Wad.from_number(200))
    collateral.flipper.approve(mcd.vat.address, approval_function=hope_directly())
    current_bid = collateral.flipper.bids(flip_kick)
    urn = mcd.vat.urn(collateral.ilk, our_address)
    assert Rad(urn.art) > current_bid.tab
    bid = Rad.from_number(6)
    TestFlipper.tend(collateral.flipper, flip_kick, our_address, current_bid.lot, bid)
    mcd.vat.can(our_address, collateral.flipper.address)
    wait(mcd, our_address, collateral.flipper.ttl()+1)
    assert collateral.flipper.deal(flip_kick).transact()

    # Raise debt from the queue (note that vow.wait is 0 on our testchain)
    bites = mcd.cat.past_bites(100)
    for bite in bites:
        era_bite = bite.era(web3)
        assert era_bite > int(datetime.now().timestamp()) - 120
        assert mcd.vow.sin_of(era_bite) > Rad(0)
        assert mcd.vow.flog(era_bite).transact()
        assert mcd.vow.sin_of(era_bite) == Rad(0)
    # Cancel out surplus and debt
    dai_vow = mcd.vat.dai(mcd.vow.address)
    assert dai_vow <= mcd.vow.woe()
    assert mcd.vow.heal(dai_vow).transact()
    assert mcd.vow.woe() >= mcd.vow.sump()


def check_active_auctions(auction: DealableAuctionContract):
    for bid in auction.active_auctions():
        assert bid.id > 0
        assert auction.kicks() >= bid.id
        assert isinstance(bid.guy, Address)
        assert bid.guy != Address("0x0000000000000000000000000000000000000000")


class TestFlipper:
    @pytest.fixture(scope="session")
    def collateral(self, mcd: DssDeployment) -> Collateral:
        return mcd.collaterals['ETH-A']

    @pytest.fixture(scope="session")
    def flipper(self, collateral, deployment_address) -> Flipper:
        return collateral.flipper

    @staticmethod
    def tend(flipper: Flipper, id: int, address: Address, lot: Wad, bid: Rad):
        assert (isinstance(flipper, Flipper))
        assert (isinstance(id, int))
        assert (isinstance(lot, Wad))
        assert (isinstance(bid, Rad))

        current_bid = flipper.bids(id)
        assert current_bid.guy != Address("0x0000000000000000000000000000000000000000")
        assert current_bid.tic > datetime.now().timestamp() or current_bid.tic == 0
        assert current_bid.end > datetime.now().timestamp()

        assert lot == current_bid.lot
        assert bid <= current_bid.tab
        assert bid > current_bid.bid
        assert (bid >= Rad(flipper.beg()) * current_bid.bid) or (bid == current_bid.tab)

        assert flipper.tend(id, lot, bid).transact(from_address=address)

    @staticmethod
    def dent(flipper: Flipper, id: int, address: Address, lot: Wad, bid: Rad):
        assert (isinstance(flipper, Flipper))
        assert (isinstance(id, int))
        assert (isinstance(lot, Wad))
        assert (isinstance(bid, Rad))

        current_bid = flipper.bids(id)
        assert current_bid.guy != Address("0x0000000000000000000000000000000000000000")
        assert current_bid.tic > datetime.now().timestamp() or current_bid.tic == 0
        assert current_bid.end > datetime.now().timestamp()

        assert bid == current_bid.bid
        assert bid == current_bid.tab
        assert lot < current_bid.lot
        assert flipper.beg() * lot <= current_bid.lot

        assert flipper.dent(id, lot, bid).transact(from_address=address)

    @staticmethod
    def last_log(flipper: Flipper):
        current_block = flipper.web3.eth.blockNumber
        return flipper.past_logs(current_block-1, current_block)[0]

    def test_getters(self, mcd, flipper):
        assert flipper.vat() == mcd.vat.address
        assert flipper.beg() > Wad.from_number(1)
        assert flipper.ttl() > 0
        assert flipper.tau() > flipper.ttl()
        assert flipper.kicks() >= 0

    def test_scenario(self, web3, mcd, collateral, flipper, our_address, other_address, deployment_address):
        # Create a vault
        kicks_before = flipper.kicks()
        ilk = collateral.ilk
        wrap_eth(mcd, deployment_address, Wad.from_number(1))
        collateral.approve(deployment_address)
        assert collateral.adapter.join(deployment_address, Wad.from_number(1)).transact(
            from_address=deployment_address)
        frob(mcd, collateral, deployment_address, dink=Wad.from_number(1), dart=Wad(0))
        dart = max_dart(mcd, collateral, deployment_address) - Wad(1)
        frob(mcd, collateral, deployment_address, dink=Wad(0), dart=dart)

        # Mint and withdraw all the Dai
        mcd.approve_dai(deployment_address)
        assert mcd.dai_adapter.exit(deployment_address, dart).transact(from_address=deployment_address)
        assert mcd.dai.balance_of(deployment_address) == dart
        assert mcd.vat.dai(deployment_address) == Rad(0)

        # Undercollateralize the vault
        to_price = Wad(Web3.toInt(collateral.pip.read())) / Wad.from_number(2)
        set_collateral_price(mcd, collateral, to_price)
        urn = mcd.vat.urn(collateral.ilk, deployment_address)
        ilk = mcd.vat.ilk(ilk.name)
        assert ilk.rate is not None
        assert ilk.spot is not None
        safe = Ray(urn.art) * mcd.vat.ilk(ilk.name).rate <= Ray(urn.ink) * ilk.spot
        assert not safe
        assert len(flipper.active_auctions()) == 0
        litter_before = mcd.cat.litter()

        # Bite the vault, which moves debt to the vow and kicks the flipper
        urn = mcd.vat.urn(collateral.ilk, deployment_address)
        assert urn.ink > Wad(0)
        art = min(urn.art, Wad(mcd.cat.dunk(ilk)))  # Wad
        tab = art * ilk.rate  # Wad
        assert tab == dart
        assert mcd.cat.can_bite(ilk, urn)
        assert mcd.cat.bite(ilk, urn).transact()
        kick = flipper.kicks()
        assert kick == kicks_before + 1
        urn = mcd.vat.urn(collateral.ilk, deployment_address)
        # Check vat, vow, and cat
        assert urn.ink == Wad(0)
        assert urn.art == dart - art
        assert mcd.vat.vice() > Rad(0)
        assert mcd.vow.sin() == Rad(tab)
        bites = mcd.cat.past_bites(1)
        assert len(bites) == 1
        last_bite = bites[0]
        assert last_bite.tab > Rad(0)
        assert last_bite.id == 1
        litter_after = mcd.cat.litter()
        assert litter_before < litter_after
        # Check the flipper
        current_bid = flipper.bids(kick)
        assert isinstance(current_bid, Flipper.Bid)
        assert current_bid.lot > Wad(0)
        assert current_bid.tab > Rad(0)
        assert current_bid.bid == Rad(0)
        # Cat doesn't incorporate the liquidation penalty (chop), but the kicker includes it.
        # Awaiting word from @dc why this is so.
        #assert last_bite.tab == current_bid.tab
        log = self.last_log(flipper)
        assert isinstance(log, Flipper.KickLog)
        assert log.id == kick
        assert log.lot == current_bid.lot
        assert log.bid == current_bid.bid
        assert log.tab == current_bid.tab
        assert log.usr == deployment_address
        assert log.gal == mcd.vow.address

        # Allow the auction to expire, and then resurrect it
        wait(mcd, our_address, flipper.tau()+1)
        assert flipper.tick(kick).transact()

        # Wrap some eth and handle approvals before bidding
        eth_required = Wad(current_bid.tab / Rad(ilk.spot)) * Wad.from_number(1.1)
        wrap_eth(mcd, other_address, eth_required)
        collateral.approve(other_address)
        assert collateral.adapter.join(other_address, eth_required).transact(from_address=other_address)
        wrap_eth(mcd, our_address, eth_required)
        collateral.approve(our_address)
        assert collateral.adapter.join(our_address, eth_required).transact(from_address=our_address)

        # Test the _tend_ phase of the auction
        flipper.approve(mcd.vat.address, approval_function=hope_directly(from_address=other_address))
        # Add Wad(1) to counter precision error converting tab from Rad to Wad
        frob(mcd, collateral, other_address, dink=eth_required, dart=Wad(current_bid.tab) + Wad(1))
        urn = mcd.vat.urn(collateral.ilk, other_address)
        assert Rad(urn.art) >= current_bid.tab
        # Bid the tab to instantly transition to dent stage
        TestFlipper.tend(flipper, kick, other_address, current_bid.lot, current_bid.tab)
        current_bid = flipper.bids(kick)
        assert current_bid.guy == other_address
        assert current_bid.bid == current_bid.tab
        assert len(flipper.active_auctions()) == 1
        check_active_auctions(flipper)
        log = self.last_log(flipper)
        assert isinstance(log, Flipper.TendLog)
        assert log.guy == current_bid.guy
        assert log.id == current_bid.id
        assert log.lot == current_bid.lot
        assert log.bid == current_bid.bid

        # Test the _dent_ phase of the auction
        flipper.approve(mcd.vat.address, approval_function=hope_directly(from_address=our_address))
        frob(mcd, collateral, our_address, dink=eth_required, dart=Wad(current_bid.tab) + Wad(1))
        lot = current_bid.lot - Wad.from_number(0.2)
        assert flipper.beg() * lot <= current_bid.lot
        assert mcd.vat.can(our_address, flipper.address)
        TestFlipper.dent(flipper, kick, our_address, lot, current_bid.tab)
        current_bid = flipper.bids(kick)
        assert current_bid.guy == our_address
        assert current_bid.bid == current_bid.tab
        assert current_bid.lot == lot
        log = self.last_log(flipper)
        assert isinstance(log, Flipper.DentLog)
        assert log.guy == current_bid.guy
        assert log.id == current_bid.id
        assert log.lot == current_bid.lot
        assert log.bid == current_bid.bid

        # Exercise _deal_ after bid has expired
        wait(mcd, our_address, flipper.ttl()+1)
        now = datetime.now().timestamp()
        assert 0 < current_bid.tic < now or current_bid.end < now
        assert flipper.deal(kick).transact(from_address=our_address)
        assert len(flipper.active_auctions()) == 0
        log = self.last_log(flipper)
        assert isinstance(log, Flipper.DealLog)
        assert log.usr == our_address

        # Grab our collateral
        collateral_before = collateral.gem.balance_of(our_address)
        assert collateral.adapter.exit(our_address, current_bid.lot).transact(from_address=our_address)
        collateral_after = collateral.gem.balance_of(our_address)
        assert collateral_before < collateral_after

        # Cleanup
        set_collateral_price(mcd, collateral, Wad.from_number(230))
        cleanup_urn(mcd, collateral, other_address)


class TestClipper:
    @pytest.fixture(scope="session")
    def collateral(self, mcd: DssDeployment) -> Collateral:
        return mcd.collaterals['ETH-B']

    @pytest.fixture(scope="session")
    def clipper(self, collateral, deployment_address) -> Clipper:
        return collateral.clipper

    @staticmethod
    def last_log(clipper: Clipper):
        current_block = clipper.web3.eth.blockNumber
        return clipper.past_logs(current_block-1, current_block)[0]

    def test_getters(self, mcd, clipper):
        assert clipper.ilk_name() == "ETH-B"
        assert clipper.kicks() == 0
        assert clipper.buf() == Ray.from_number(1.50)
        assert clipper.tail() == 10800
        assert clipper.cusp() == Ray.from_number(0.3333)
        assert clipper.chip() == Wad.from_number(0.02)
        assert clipper.tip() == Rad.from_number(100)

    # @pytest.mark.skip("need to fully liquidate the urn before running flapper tests")
    def test_scenario(self, web3, mcd, collateral, clipper, our_address, other_address, deployment_address):
        dirt_before = mcd.dog.dog_dirt()
        vice_before = mcd.vat.vice()
        sin_before = mcd.vow.sin()

        # Create a vault
        ilk = collateral.ilk
        wrap_eth(mcd, deployment_address, Wad.from_number(1))
        collateral.approve(deployment_address)
        assert collateral.adapter.join(deployment_address, Wad.from_number(1)).transact(
            from_address=deployment_address)
        frob(mcd, collateral, deployment_address, dink=Wad.from_number(1), dart=Wad(0))
        dart = max_dart(mcd, collateral, deployment_address) - Wad(1)
        frob(mcd, collateral, deployment_address, dink=Wad(0), dart=dart)

        # Mint and withdraw all the Dai
        mcd.approve_dai(deployment_address)
        assert mcd.dai_adapter.exit(deployment_address, dart).transact(from_address=deployment_address)
        assert mcd.vat.dai(deployment_address) == Rad(0)

        # Undercollateralize the vault
        to_price = Wad(Web3.toInt(collateral.pip.read())) / Wad.from_number(2)
        set_collateral_price(mcd, collateral, to_price)
        urn = mcd.vat.urn(collateral.ilk, deployment_address)
        ilk = mcd.vat.ilk(ilk.name)
        assert ilk.rate is not None
        assert ilk.spot is not None
        safe = Ray(urn.art) * mcd.vat.ilk(ilk.name).rate <= Ray(urn.ink) * ilk.spot
        assert not safe
        assert clipper.active_count() == 0

        # Bark the vault, which moves debt to the vow and kicks the clipper
        urn = mcd.vat.urn(collateral.ilk, deployment_address)
        assert urn.ink > Wad(0)
        tab = urn.art * ilk.rate  # Wad
        assert tab == dart
        assert mcd.dog.bark(ilk, urn).transact()
        barks = mcd.dog.past_barks(1)
        assert len(barks) == 1
        last_bite = barks[0]
        assert last_bite.due > Rad(0)
        assert clipper.active_count() == 1
        kick = clipper.kicks()
        assert kick == 1
        urn = mcd.vat.urn(collateral.ilk, deployment_address)
        (done, price) = clipper.status(kick)
        assert not done
        assert price == Ray.from_number(172.5)
        # Check vat, vow, and dog
        assert urn.ink == Wad(0)
        assert vice_before < mcd.vat.vice()
        assert sin_before < mcd.vow.sin()
        assert dirt_before < mcd.dog.dog_dirt()
        # Check the clipper
        current_sale = clipper.sales(kick)
        assert isinstance(current_sale, Clipper.Sale)
        assert current_sale.pos == 0
        assert round(current_sale.tab) == Rad.from_number(105)
        assert current_sale.lot == Wad.from_number(1)
        assert current_sale.usr == deployment_address
        assert current_sale.tic > 0
        assert round(current_sale.top, 1) == price
        kick_log = self.last_log(clipper)
        assert isinstance(kick_log, Clipper.KickLog)
        assert kick_log.id == kick
        assert kick_log.top == current_sale.top
        assert kick_log.tab == current_sale.tab
        assert kick_log.lot == current_sale.lot
        assert kick_log.usr == deployment_address
        assert kick_log.kpr == our_address
        assert kick_log.coin == Rad(clipper.tip() + (current_sale.tab * clipper.chip()))
        (done, price) = clipper.status(kick)
        assert not done

        # TODO: Allow the auction to expire, and then resurrect it
        # wait(mcd, our_address, clipper.tau()+1)
        # assert clipper.redo(kick).transact()

        # Wrap some eth and handle approvals before bidding
        eth_required = Wad(current_sale.tab / Rad(ilk.spot)) * Wad.from_number(1.1)
        wrap_eth(mcd, other_address, eth_required)
        collateral.approve(other_address)
        assert collateral.adapter.join(other_address, eth_required).transact(from_address=other_address)
        wrap_eth(mcd, our_address, eth_required)
        collateral.approve(our_address)
        assert collateral.adapter.join(our_address, eth_required).transact(from_address=our_address)
        clipper.approve(mcd.vat.address, approval_function=hope_directly(from_address=our_address))

        # Ensure we cannot take collateral below the top price (150.9375)
        with pytest.raises(AssertionError):
            clipper.validate_take(kick, Wad.from_number(1), Ray.from_number(140))
        assert not clipper.take(kick, Wad.from_number(1), Ray.from_number(140)).transact(from_address=our_address)
        # Ensure validation fails if we have insufficient Dai for our bid
        with pytest.raises(AssertionError):
            clipper.validate_take(kick, Wad.from_number(1), Ray.from_number(180))
        assert not clipper.take(kick, Wad.from_number(1), Ray.from_number(180)).transact(from_address=our_address)

        # Take some collateral with max above the top price
        (done, price) = clipper.status(kick)
        assert not done
        clipper.validate_take(kick, Wad.from_number(0.3), Ray.from_number(180))
        assert clipper.take(kick, Wad.from_number(0.3), Ray.from_number(180)).transact(from_address=our_address)
        (done, price) = clipper.status(kick)
        assert not done
        current_sale = clipper.sales(kick)
        assert current_sale.lot == Wad.from_number(0.7)
        assert current_sale.top > price
        assert current_sale.tab < kick_log.tab
        first_take_log = self.last_log(clipper)
        assert first_take_log.id == 1
        assert first_take_log.max == Ray.from_number(180)
        assert first_take_log.price == price
        assert first_take_log.lot == current_sale.lot
        assert round(first_take_log.owe, 18) == round(Rad.from_number(0.3) * Rad(price), 18)

        # Sleep until price has gone down enough to bid with remaining Dai
        dai = mcd.vat.dai(our_address)
        last_price = price
        while price * Ray(current_sale.lot) > Ray(dai):
            print(f"Bid cost {price * Ray(current_sale.lot)} exceeds Dai balance {dai}")
            time_travel_by(web3, 1)
            (done, price) = clipper.status(kick)
            assert price < last_price
            assert not done
            last_price = price
        clipper.validate_take(kick, current_sale.lot, price)
        assert clipper.take(kick, current_sale.lot, price).transact(from_address=our_address)
        current_sale = clipper.sales(kick)
        assert current_sale.lot == Wad(0)
        assert current_sale.tab == Rad(0)
        # TODO: Determine why auction isn't "done" even if collateral has been taken
        #(done, price) = clipper.status(kick)
        #assert done

        # Ensure we can retrieve our collateral
        collateral_before = collateral.gem.balance_of(our_address)
        assert collateral.adapter.exit(our_address, Wad.from_number(0.5)).transact(from_address=our_address)
        collateral_after = collateral.gem.balance_of(our_address)
        assert collateral_before < collateral_after

        # Cleanup
        set_collateral_price(mcd, collateral, Wad.from_number(230))
        cleanup_urn(mcd, collateral, other_address)


class TestFlapper:
    @pytest.fixture(scope="session")
    def flapper(self, mcd: DssDeployment) -> Flapper:
        return mcd.flapper

    @staticmethod
    def tend(flapper: Flapper, id: int, address: Address, lot: Rad, bid: Wad):
        assert (isinstance(flapper, Flapper))
        assert (isinstance(id, int))
        assert (isinstance(lot, Rad))
        assert (isinstance(bid, Wad))

        assert flapper.live() == 1

        current_bid = flapper.bids(id)
        assert current_bid.guy != Address("0x0000000000000000000000000000000000000000")
        assert current_bid.tic > datetime.now().timestamp() or current_bid.tic == 0
        assert current_bid.end > datetime.now().timestamp()

        assert lot == current_bid.lot
        assert bid > current_bid.bid
        assert bid >= flapper.beg() * current_bid.bid

        assert flapper.tend(id, lot, bid).transact(from_address=address)
        log = TestFlapper.last_log(flapper)
        assert isinstance(log, Flapper.TendLog)
        assert log.guy == address
        assert log.id == id
        assert log.lot == lot
        assert log.bid == bid

    @staticmethod
    def last_log(flapper: Flapper):
        current_block = flapper.web3.eth.blockNumber
        return flapper.past_logs(current_block-1, current_block)[0]

    def test_getters(self, mcd, flapper):
        assert flapper.vat() == mcd.vat.address
        assert flapper.beg() > Wad.from_number(1)
        assert flapper.ttl() > 0
        assert flapper.tau() > flapper.ttl()
        assert flapper.kicks() >= 0

    def test_scenario(self, web3, mcd, flapper, our_address, other_address, deployment_address):
        create_surplus(mcd, flapper, deployment_address)

        joy_before = mcd.vat.dai(mcd.vow.address)
        # total surplus > total debt + surplus auction lot size + surplus buffer
        assert joy_before > mcd.vat.sin(mcd.vow.address) + mcd.vow.bump() + mcd.vow.hump()
        assert (mcd.vat.sin(mcd.vow.address) - mcd.vow.sin()) - mcd.vow.ash() == Rad(0)
        assert mcd.vow.flap().transact()
        kick = flapper.kicks()
        assert kick == 1
        assert len(flapper.active_auctions()) == 1
        check_active_auctions(flapper)
        current_bid = flapper.bids(1)
        assert current_bid.lot > Rad(0)
        log = self.last_log(flapper)
        assert isinstance(log, Flapper.KickLog)
        assert log.id == kick
        assert log.lot == current_bid.lot
        assert log.bid == current_bid.bid

        # Allow the auction to expire, and then resurrect it
        wait(mcd, our_address, flapper.tau()+1)
        assert flapper.tick(kick).transact()

        # Bid on the resurrected auction
        mint_mkr(mcd.mkr, our_address, Wad.from_number(10))
        flapper.approve(mcd.mkr.address, directly(from_address=our_address))
        bid = Wad.from_number(0.001)
        assert mcd.mkr.balance_of(our_address) > bid
        TestFlapper.tend(flapper, kick, our_address, current_bid.lot, bid)
        current_bid = flapper.bids(kick)
        assert current_bid.bid == bid
        assert current_bid.guy == our_address

        # Exercise _deal_ after bid has expired
        wait(mcd, our_address, flapper.ttl()+1)
        now = datetime.now().timestamp()
        assert 0 < current_bid.tic < now or current_bid.end < now
        assert flapper.deal(kick).transact(from_address=our_address)
        joy_after = mcd.vat.dai(mcd.vow.address)
        print(f'joy_before={str(joy_before)}, joy_after={str(joy_after)}')
        assert joy_before - joy_after == mcd.vow.bump()
        log = self.last_log(flapper)
        assert isinstance(log, Flapper.DealLog)
        assert log.usr == our_address
        assert log.id == kick

        # Grab our dai
        mcd.approve_dai(our_address)
        assert mcd.dai_adapter.exit(our_address, Wad(current_bid.lot)).transact(from_address=our_address)
        assert mcd.dai.balance_of(our_address) >= Wad(current_bid.lot)
        assert (mcd.vat.sin(mcd.vow.address) - mcd.vow.sin()) - mcd.vow.ash() == Rad(0)


class TestFlopper:
    @pytest.fixture(scope="session")
    def flopper(self, mcd: DssDeployment) -> Flopper:
        return mcd.flopper

    @staticmethod
    def dent(flopper: Flopper, id: int, address: Address, lot: Wad, bid: Rad):
        assert (isinstance(flopper, Flopper))
        assert (isinstance(id, int))
        assert (isinstance(lot, Wad))
        assert (isinstance(bid, Rad))

        assert flopper.live() == 1

        current_bid = flopper.bids(id)
        assert current_bid.guy != Address("0x0000000000000000000000000000000000000000")
        assert current_bid.tic > datetime.now().timestamp() or current_bid.tic == 0
        assert current_bid.end > datetime.now().timestamp()

        assert bid == current_bid.bid
        assert Wad(0) < lot < current_bid.lot
        assert flopper.beg() * lot <= current_bid.lot

        assert flopper.dent(id, lot, bid).transact(from_address=address)
        log = TestFlopper.last_log(flopper)
        assert isinstance(log, Flopper.DentLog)
        assert log.guy == address
        assert log.id == id
        assert log.lot == lot
        assert log.bid == bid

    @staticmethod
    def last_log(flopper: Flopper):
        current_block = flopper.web3.eth.blockNumber
        return flopper.past_logs(current_block-1, current_block)[0]

    def test_getters(self, mcd, flopper):
        assert flopper.vat() == mcd.vat.address
        assert flopper.beg() > Wad.from_number(1)
        assert flopper.ttl() > 0
        assert flopper.tau() > flopper.ttl()
        assert flopper.kicks() >= 0

    def test_scenario(self, web3, mcd, flopper, our_address, other_address, deployment_address):
        create_debt(web3, mcd, our_address, deployment_address)

        # Kick off the flop auction
        assert flopper.kicks() == 0
        assert len(flopper.active_auctions()) == 0
        assert mcd.vat.dai(mcd.vow.address) == Rad(0)
        assert mcd.vow.flop().transact()
        kick = flopper.kicks()
        assert kick == 1
        assert len(flopper.active_auctions()) == 1
        check_active_auctions(flopper)
        current_bid = flopper.bids(kick)
        log = self.last_log(flopper)
        assert isinstance(log, Flopper.KickLog)
        assert log.id == kick
        assert log.lot == current_bid.lot
        assert log.bid == current_bid.bid
        assert log.gal == mcd.vow.address

        # Allow the auction to expire, and then resurrect it
        wait(mcd, our_address, flopper.tau()+1)
        assert flopper.tick(kick).transact()
        assert flopper.bids(kick).lot == current_bid.lot * flopper.pad()

        # Bid on the resurrected auction
        bid = Wad.from_number(0.000005)
        flopper.approve(mcd.vat.address, hope_directly())
        assert mcd.vat.can(our_address, flopper.address)
        TestFlopper.dent(flopper, kick, our_address, bid, current_bid.bid)
        current_bid = flopper.bids(kick)
        assert current_bid.guy == our_address

        # Confirm victory
        wait(mcd, our_address, flopper.ttl()+1)
        assert flopper.live()
        now = int(datetime.now().timestamp())
        assert (current_bid.tic < now and current_bid.tic != 0) or current_bid.end < now
        mkr_before = mcd.mkr.balance_of(our_address)
        assert flopper.deal(kick).transact(from_address=our_address)
        mkr_after = mcd.mkr.balance_of(our_address)
        assert mkr_after > mkr_before
        log = self.last_log(flopper)
        assert isinstance(log, Flopper.DealLog)
        assert log.usr == our_address
        assert log.id == kick
