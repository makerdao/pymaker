# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2018-2019 bargst, EdNoepel
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

import json
import pytest
import time
from datetime import datetime
from web3 import Web3

from pymaker import Address
from pymaker.approval import hope_directly
from pymaker.deployment import Collateral, DssDeployment
from pymaker.dss import Ilk, Urn, Vat, Vow
from pymaker.feed import DSValue
from pymaker.join import DaiJoin, GemJoin, GemJoin5
from pymaker.numeric import Wad, Ray, Rad
from pymaker.oracles import OSM
from pymaker.token import DSToken, DSEthToken, ERC20Token
from tests.conftest import validate_contracts_loaded


@pytest.fixture
def urn(our_address: Address, mcd: DssDeployment):
    collateral = mcd.collaterals['ETH-A']
    urn = mcd.vat.urn(collateral.ilk, our_address)
    assert urn.ilk is not None
    assert urn.ilk == collateral.ilk
    return urn


def wrap_eth(mcd: DssDeployment, address: Address, amount: Wad):
    assert isinstance(mcd, DssDeployment)
    assert isinstance(address, Address)
    assert isinstance(amount, Wad)
    assert amount > Wad(0)

    collateral = mcd.collaterals['ETH-A']
    assert isinstance(collateral.gem, DSEthToken)
    assert collateral.gem.deposit(amount).transact(from_address=address)


def mint_mkr(mkr: DSToken, recipient_address: Address, amount: Wad):
    assert isinstance(mkr, DSToken)
    assert isinstance(recipient_address, Address)
    assert isinstance(amount, Wad)
    assert amount > Wad(0)

    deployment_address = Address("0x00a329c0648769A73afAc7F9381E08FB43dBEA72")
    assert mkr.mint(amount).transact(from_address=deployment_address)
    assert mkr.balance_of(deployment_address) > Wad(0)
    assert mkr.approve(recipient_address).transact(from_address=deployment_address)
    assert mkr.transfer(recipient_address, amount).transact(from_address=deployment_address)


def get_collateral_price(collateral: Collateral):
    assert isinstance(collateral, Collateral)
    return Wad(Web3.toInt(collateral.pip.read()))


def set_collateral_price(mcd: DssDeployment, collateral: Collateral, price: Wad):
    assert isinstance(mcd, DssDeployment)
    assert isinstance(collateral, Collateral)
    assert isinstance(price, Wad)
    assert price > Wad(0)

    pip = collateral.pip
    assert isinstance(pip, DSValue)

    print(f"Changing price of {collateral.ilk.name} to {price}")
    assert pip.poke_with_int(price.value).transact(from_address=pip.get_owner())
    assert mcd.spotter.poke(ilk=collateral.ilk).transact(from_address=pip.get_owner())

    assert get_collateral_price(collateral) == price


def frob(mcd: DssDeployment, collateral: Collateral, address: Address, dink: Wad, dart: Wad):
    """Wraps vat.frob for debugging purposes"""
    # given
    assert isinstance(mcd, DssDeployment)
    assert isinstance(collateral, Collateral)
    assert isinstance(address, Address)
    assert isinstance(dink, Wad)
    assert isinstance(dart, Wad)
    ilk = collateral.ilk

    # when
    ink_before = mcd.vat.urn(ilk, address).ink
    art_before = mcd.vat.urn(ilk, address).art

    # then
    if dart < Wad(0):
        assert mcd.vat.dai(address) >= Rad(dart*-1)
    assert mcd.vat.frob(ilk=ilk, urn_address=address, dink=dink, dart=dart).transact(from_address=address)
    assert mcd.vat.urn(ilk, address).ink == ink_before + dink
    assert mcd.vat.urn(ilk, address).art == art_before + dart


def max_dart(mcd: DssDeployment, collateral: Collateral, our_address: Address) -> Wad:
    """Determines how much stablecoin should be reserved in an `urn` to make it as poorly collateralized as
    possible, such that a small change to the collateral price could trip the liquidation ratio."""
    assert isinstance(mcd, DssDeployment)
    assert isinstance(collateral, Collateral)
    assert isinstance(our_address, Address)

    urn = mcd.vat.urn(collateral.ilk, our_address)
    ilk = mcd.vat.ilk(collateral.ilk.name)

    # change in art = (collateral balance * collateral price with safety margin) - CDP's stablecoin debt
    dart = urn.ink * ilk.spot - Wad(Ray(urn.art) * ilk.rate)

    # change in debt must also take the rate into account
    dart = dart * Wad(Ray.from_number(1) / ilk.rate)

    # prevent the change in debt from exceeding the collateral debt ceiling
    if (Rad(urn.art) + Rad(dart)) >= ilk.line:
        print("max_dart is avoiding collateral debt ceiling")
        dart = Wad(ilk.line - Rad(urn.art))

    # prevent the change in debt from exceeding the total debt ceiling
    debt = mcd.vat.debt() + Rad(ilk.rate * dart)
    line = Rad(ilk.line)
    if (debt + Rad(dart)) >= line:
        print("max_dart is avoiding total debt ceiling")
        dart = Wad(debt - Rad(urn.art))

    assert dart > Wad(0)
    return dart


def cleanup_urn(mcd: DssDeployment, collateral: Collateral, address: Address):
    assert isinstance(mcd, DssDeployment)
    assert isinstance(collateral, Collateral)
    assert isinstance(address, Address)
    urn = mcd.vat.urn(collateral.ilk, address)
    ilk = mcd.vat.ilk(collateral.ilk.name)

    # If jug.drip has been called, we won't have sufficient dai to repay the CDP
    if ilk.rate > Ray.from_number(1):
        return

    # Repay borrowed Dai
    mcd.approve_dai(address)
    # Put all the user's Dai back into the vat
    if mcd.dai.balance_of(address) >= Wad(0):
        assert mcd.dai_adapter.join(address, mcd.dai.balance_of(address)).transact(from_address=address)
    # tab = Ray(urn.art) * ilk.rate
    # print(f'tab={str(tab)}, rate={str(ilk.rate)}, dai={str(mcd.vat.dai(address))}')
    if urn.art > Wad(0) and mcd.vat.dai(address) >= Rad(urn.art):
        frob(mcd, collateral, address, Wad(0), urn.art * -1)

    # Withdraw collateral
    collateral.approve(address)
    urn = mcd.vat.urn(collateral.ilk, address)
    # dink = Wad((Ray(urn.art) * ilk.rate) / ilk.spot)
    # print(f'dink={str(dink)}, ink={str(urn.ink)}')
    if urn.art == Wad(0) and urn.ink > Wad(0):
        frob(mcd, collateral, address, urn.ink * -1, Wad(0))
    assert collateral.adapter.exit(address, mcd.vat.gem(collateral.ilk, address)).transact(from_address=address)
    # TestVat.ensure_clean_urn(mcd, collateral, address)


@pytest.fixture(scope="session")
def bite(web3: Web3, mcd: DssDeployment, our_address: Address):
    collateral = mcd.collaterals['ETH-A']

    # Add collateral to our CDP
    dink = Wad.from_number(1)
    wrap_eth(mcd, our_address, dink)
    assert collateral.gem.balance_of(our_address) >= dink
    assert collateral.adapter.join(our_address, dink).transact()
    frob(mcd, collateral, our_address, dink, Wad(0))

    # Define required bite parameters
    to_price = Wad(Web3.toInt(collateral.pip.read())) / Wad.from_number(2)

    # Manipulate price to make our CDP underwater
    # Note this will only work on a testchain deployed with fixed prices, where PIP is a DSValue
    frob(mcd, collateral, our_address, Wad(0), max_dart(mcd, collateral, our_address))
    set_collateral_price(mcd, collateral, to_price)

    # Bite the CDP
    assert mcd.cat.can_bite(collateral.ilk, Urn(our_address))
    assert mcd.cat.bite(collateral.ilk, Urn(our_address)).transact()


@pytest.fixture(scope="session")
def bite_event(web3: Web3, mcd: DssDeployment, our_address: Address):
    bite(web3, mcd, our_address)
    # Return the corresponding event
    return mcd.cat.past_bites(1)[0]


class TestConfig:
    def test_from_json(self, web3: Web3, mcd: DssDeployment):
        # fixture calls DssDeployment.from_json
        assert len(mcd.config.collaterals) >= 3
        assert len(mcd.collaterals) >= 3
        assert len(mcd.config.to_dict()) > 10
        assert len(mcd.collaterals) == len(mcd.config.collaterals)

    def test_to_json(self, web3: Web3, mcd: DssDeployment):
        config_out = mcd.to_json()
        dict = json.loads(config_out)
        assert "MCD_GOV" in dict
        assert "MCD_DAI" in dict
        assert len(dict) > 20

    def test_from_node(self, web3: Web3):
        mcd_testnet = DssDeployment.from_node(web3)
        validate_contracts_loaded(mcd_testnet)

    def test_collaterals(self, mcd):
        for collateral in mcd.collaterals.values():
            assert isinstance(collateral.ilk, Ilk)
            assert isinstance(collateral.gem, ERC20Token)
            assert len(collateral.ilk.name) > 0
            assert len(collateral.gem.name()) > 0
            assert len(collateral.gem.symbol()) > 0
            assert collateral.adapter
            assert collateral.flipper or collateral.clipper
            assert collateral.pip

    def test_account_transfers(self, web3: Web3, mcd, our_address, other_address):
        print(mcd.collaterals)
        collateral = mcd.collaterals['ETH-A']
        token = collateral.gem
        amount = Wad(10)

        assert web3.eth.defaultAccount == our_address.address
        assert our_address != other_address
        wrap_eth(mcd, our_address, amount)

        # Move eth between each account to confirm keys are properly set up
        before = token.balance_of(our_address)
        assert token.transfer_from(our_address, other_address, amount).transact()
        after = token.balance_of(our_address)
        assert (before - amount) == after

        assert token.transfer_from(other_address, our_address, amount).transact(from_address=other_address)
        assert token.balance_of(our_address) == before

    def test_get_active_auctions(self, mcd):
        auctions = mcd.active_auctions()
        assert "flips" in auctions
        assert "flaps" in auctions
        assert "flops" in auctions


class TestVat:
    @staticmethod
    def ensure_clean_urn(mcd: DssDeployment, collateral: Collateral, address: Address):
        assert isinstance(mcd, DssDeployment)
        assert isinstance(collateral, Collateral)
        assert isinstance(address, Address)

        urn = mcd.vat.urn(collateral.ilk, address)
        assert urn.ink == Wad(0)
        assert urn.art == Wad(0)
        assert mcd.vat.gem(collateral.ilk, address) == Wad(0)

    def test_getters(self, mcd):
        assert isinstance(mcd.vat.live(), bool)

    def test_ilk(self, mcd):
        assert mcd.vat.ilk('XXX') == Ilk('XXX',
                                         rate=Ray(0), ink=Wad(0), art=Wad(0), spot=Ray(0), line=Rad(0), dust=Rad(0))

        ilk = mcd.collaterals["ETH-C"].ilk
        assert ilk.line == Rad.from_number(15000000)
        assert ilk.dust == Rad(0)

        representation = repr(ilk)
        assert "ETH-C" in representation

    def test_gem(self, web3: Web3, mcd: DssDeployment, our_address: Address):
        # given
        collateral = mcd.collaterals['ETH-A']
        amount_to_join = Wad(10)
        our_urn = mcd.vat.urn(collateral.ilk, our_address)
        assert isinstance(collateral.ilk, Ilk)
        assert isinstance(collateral.adapter, GemJoin)
        assert collateral.ilk.name == collateral.adapter.ilk().name
        assert our_urn.address == our_address
        wrap_eth(mcd, our_address, amount_to_join)
        assert collateral.gem.balance_of(our_address) >= amount_to_join

        # when
        before_join = mcd.vat.gem(collateral.ilk, our_urn.address)
        collateral.approve(our_address)
        assert collateral.adapter.join(our_address, amount_to_join).transact()
        after_join = mcd.vat.gem(collateral.ilk, our_urn.address)
        assert collateral.adapter.exit(our_address, amount_to_join).transact()
        after_exit = mcd.vat.gem(collateral.ilk, our_urn.address)

        # then
        assert after_join - before_join == amount_to_join
        assert after_exit == before_join

    def test_gem_join(self, mcd: DssDeployment):
        collateral_bat = mcd.collaterals['BAT-A']
        assert isinstance(collateral_bat.adapter, GemJoin)
        assert collateral_bat.adapter.dec() == 18

        collateral_usdc = mcd.collaterals['USDC-A']
        assert isinstance(collateral_usdc.adapter, GemJoin5)
        assert collateral_usdc.adapter.dec() == 6

    def test_dai(self, mcd, urn):
        dai = mcd.vat.dai(urn.address)
        assert dai >= Rad(0)

    def test_sin(self, mcd, urn):
        sin = mcd.vat.sin(urn.address)
        assert isinstance(sin, Rad)
        assert sin == Rad(0)

    def test_debt(self, mcd):
        debt = mcd.vat.debt()
        assert debt >= Rad(0)
        assert debt < mcd.vat.line()

    def test_urn(self, urn):
        time.sleep(11)
        assert urn.ilk is not None
        urn_bytes = urn.toBytes()
        urn_from_bytes = urn.fromBytes(urn_bytes)
        assert urn_from_bytes.address == urn.address

    def test_frob_noop(self, mcd, our_address):
        # given
        collateral = mcd.collaterals['ETH-A']
        our_urn = mcd.vat.urn(collateral.ilk, our_address)

        # when
        assert mcd.vat.frob(collateral.ilk, our_address, Wad(0), Wad(0)).transact()

        # then
        assert mcd.vat.urn(collateral.ilk, our_address) == our_urn

    def test_frob_add_ink(self, mcd, our_address):
        # given
        collateral = mcd.collaterals['ETH-A']
        our_urn = mcd.vat.urn(collateral.ilk, our_address)

        # when
        wrap_eth(mcd, our_address, Wad(10))
        assert collateral.adapter.join(our_address, Wad(10)).transact()
        assert mcd.vat.frob(collateral.ilk, our_address, Wad(10), Wad(0)).transact()

        # then
        assert mcd.vat.urn(collateral.ilk, our_address).ink == our_urn.ink + Wad(10)

        # rollback
        cleanup_urn(mcd, collateral, our_address)

    def test_frob_add_art(self, mcd, our_address: Address):
        # given
        collateral = mcd.collaterals['ETH-A']
        our_urn = mcd.vat.urn(collateral.ilk, our_address)

        # when
        wrap_eth(mcd, our_address, Wad.from_number(10))
        assert collateral.adapter.join(our_address, Wad.from_number(3)).transact()
        assert mcd.vat.frob(collateral.ilk, our_address, Wad.from_number(3), Wad.from_number(24)).transact()

        # then
        assert mcd.vat.urn(collateral.ilk, our_address).art == our_urn.art + Wad.from_number(24)

        # rollback
        cleanup_urn(mcd, collateral, our_address)

    def test_frob_other_account(self, web3, mcd, other_address):
        # given
        collateral = mcd.collaterals['ETH-A']
        collateral.approve(other_address)
        mcd.dai_adapter.approve(hope_directly(from_address=other_address), mcd.vat.address)
        urn = mcd.vat.urn(collateral.ilk, other_address)
        assert urn.address == other_address

        # when
        wrap_eth(mcd, other_address, Wad.from_number(10))
        assert collateral.gem.balance_of(other_address) >= Wad.from_number(10)
        assert collateral.gem == collateral.adapter.gem()
        collateral.gem.approve(collateral.adapter.address)
        assert collateral.adapter.join(other_address, Wad.from_number(3)).transact(from_address=other_address)
        assert mcd.vat.frob(collateral.ilk, other_address, Wad.from_number(3), Wad.from_number(20)).transact(from_address=other_address)

        # then
        assert mcd.vat.urn(collateral.ilk, other_address).art == urn.art + Wad.from_number(20)

        # rollback
        cleanup_urn(mcd, collateral, other_address)

    def test_past_frob(self, mcd, our_address, other_address):
        # given
        collateral0 = mcd.collaterals['ETH-B']
        ilk0 = collateral0.ilk
        collateral1 = mcd.collaterals['ETH-C']
        ilk1 = collateral1.ilk

        try:
            # when
            wrap_eth(mcd, our_address, Wad.from_number(18))
            wrap_eth(mcd, other_address, Wad.from_number(18))

            collateral0.approve(our_address)
            assert collateral0.adapter.join(our_address, Wad.from_number(9)).transact()
            assert mcd.vat.frob(ilk0, our_address, Wad.from_number(3), Wad.from_number(0)).transact()

            collateral1.approve(other_address)
            assert collateral1.adapter.join(other_address, Wad.from_number(9)).transact(from_address=other_address)
            assert mcd.vat.frob(ilk1, other_address, Wad.from_number(9), Wad.from_number(0)).transact(from_address=other_address)
            assert mcd.vat.frob(ilk1, other_address, Wad.from_number(-3), Wad.from_number(0)).transact(from_address=other_address)

            assert mcd.vat.frob(ilk1, our_address, Wad.from_number(3), Wad.from_number(0),
                                collateral_owner=other_address, dai_recipient=other_address).transact(
                from_address=other_address)

            # then
            current_block = mcd.web3.eth.blockNumber
            from_block = current_block - 6
            frobs = mcd.vat.past_frobs(from_block)
            assert len(frobs) == 4
            assert frobs[0].ilk == ilk0.name
            assert frobs[0].urn == our_address
            assert frobs[0].dink == Wad.from_number(3)
            assert frobs[0].dart == Wad(0)
            assert frobs[1].ilk == ilk1.name
            assert frobs[1].urn == other_address
            assert frobs[1].dink == Wad.from_number(9)
            assert frobs[1].dart == Wad(0)
            assert frobs[2].ilk == ilk1.name
            assert frobs[2].urn == other_address
            assert frobs[2].dink == Wad.from_number(-3)
            assert frobs[2].dart == Wad(0)
            assert frobs[3].urn == our_address
            assert frobs[3].collateral_owner == other_address
            assert frobs[3].dink == Wad.from_number(3)
            assert frobs[3].dart == Wad(0)

            assert len(mcd.vat.past_frobs(from_block, ilk=ilk0)) == 1
            assert len(mcd.vat.past_frobs(from_block, ilk=ilk1)) == 3
            assert len(mcd.vat.past_frobs(from_block, ilk=mcd.collaterals['USDC-A'].ilk)) == 0

        finally:
            # teardown
            cleanup_urn(mcd, collateral0, our_address)
            cleanup_urn(mcd, collateral1, other_address)

    def test_heal(self, mcd):
        assert mcd.vat.heal(Rad(0)).transact()

    def test_flux(self, mcd, our_address, other_address):
        # given
        collateral = mcd.collaterals['ETH-A']
        collateral.approve(our_address)
        other_balance_before = mcd.vat.gem(collateral.ilk, other_address)
        amount = Wad.from_number(3)
        wrap_eth(mcd, our_address, amount)
        assert collateral.adapter.join(our_address, amount).transact()

        # when
        assert mcd.vat.flux(collateral.ilk, our_address, other_address, amount).transact()

        # then
        other_balance_after = mcd.vat.gem(collateral.ilk, other_address)
        assert Wad(other_balance_before) + amount == Wad(other_balance_after)

        # teardown
        cleanup_urn(mcd, collateral, our_address)

    def test_move(self, mcd, our_address, other_address):
        # given
        collateral = mcd.collaterals['ETH-A']
        collateral.approve(our_address)
        our_urn = mcd.vat.urn(collateral.ilk, our_address)
        wrap_eth(mcd, our_address, Wad.from_number(10))
        assert collateral.adapter.join(our_address, Wad.from_number(3)).transact()
        assert mcd.vat.frob(collateral.ilk, our_address, Wad.from_number(3), Wad.from_number(30)).transact()
        other_balance_before = mcd.vat.dai(other_address)

        # when
        assert mcd.vat.move(our_address, other_address, Rad.from_number(30)).transact()

        # then
        other_balance_after = mcd.vat.dai(other_address)
        assert other_balance_before + Rad.from_number(30) == other_balance_after

        # confirm log was emitted and could be parsed
        from_block = mcd.web3.eth.blockNumber
        logs = mcd.vat.past_logs(from_block)
        assert isinstance(logs[0], Vat.LogMove)
        logmove: Vat.LogMove = logs[0]
        assert logmove.src == our_address
        assert logmove.dst == other_address
        assert logmove.dart == Rad.from_number(30)

        # rollback
        cleanup_urn(mcd, collateral, our_address)

    def test_fork(self, mcd, our_address, other_address):
        # given
        collateral = mcd.collaterals['ETH-A']
        mcd.vat.hope(our_address).transact(from_address=other_address)
        mcd.vat.hope(other_address).transact(from_address=our_address)

        our_urn = mcd.vat.urn(collateral.ilk, our_address)
        wrap_eth(mcd, our_address, Wad.from_number(6))
        assert collateral.adapter.join(our_address, Wad.from_number(6)).transact()
        assert mcd.vat.frob(collateral.ilk, our_address, Wad.from_number(6), Wad.from_number(40)).transact()
        urn_before = mcd.vat.urn(collateral.ilk, other_address)

        # when
        assert mcd.vat.fork(collateral.ilk, our_address, other_address, Wad.from_number(3), Wad.from_number(20)).transact()

        # then
        urn_after = mcd.vat.urn(collateral.ilk, other_address)
        assert urn_before.ink + Wad.from_number(3) == urn_after.ink
        assert urn_before.art + Wad.from_number(20) == urn_after.art

        # confirm log was emitted and could be parsed
        from_block = mcd.web3.eth.blockNumber
        logs = mcd.vat.past_logs(from_block)
        assert isinstance(logs[0], Vat.LogFork)
        logfork: Vat.LogFork = logs[0]
        assert logfork.ilk == collateral.ilk.name
        assert logfork.src == our_address
        assert logfork.dst == other_address
        assert logfork.dink == Wad.from_number(3)
        assert logfork.dart == Wad.from_number(20)

        # rollback
        cleanup_urn(mcd, collateral, our_address)


class TestCat:
    def test_getters(self, mcd):
        assert isinstance(mcd.cat.live(), bool)
        assert isinstance(mcd.cat.vat, Vat)
        assert isinstance(mcd.cat.vow, Vow)

        collateral = mcd.collaterals['ETH-C']
        assert not collateral.clipper
        assert mcd.cat.flipper(collateral.ilk) == collateral.flipper.address
        assert mcd.cat.chop(collateral.ilk) == Wad.from_number(1.05)
        assert mcd.cat.dunk(collateral.ilk) == Rad.from_number(1000)
        assert mcd.cat.box() == Rad.from_number(5000)


class TestDog:
    def test_getters(self, mcd):
        assert isinstance(mcd.dog.live(), bool)
        assert isinstance(mcd.cat.vat, Vat)
        assert isinstance(mcd.cat.vow, Vow)

        collateral = mcd.collaterals['ETH-B']
        assert not collateral.flipper
        assert mcd.dog.clipper(collateral.ilk) == collateral.clipper.address
        assert mcd.dog.chop(collateral.ilk) == Wad.from_number(1.05)
        assert mcd.dog.hole(collateral.ilk) == Rad.from_number(300)
        assert mcd.dog.dirt(collateral.ilk) == Rad(0)
        assert mcd.dog.dog_hole() == Rad.from_number(5000)
        assert mcd.dog.dog_dirt() == Rad(0)


class TestSpotter:
    def test_mat(self, mcd):
        val = Ray(mcd.collaterals['ETH-A'].pip.read_as_int())

        ilk = mcd.vat.ilk('ETH-A')
        par = mcd.spotter.par()
        mat = mcd.spotter.mat(ilk)

        assert mat == (Ray(val * 10 ** 9) / par) / (ilk.spot)


class TestVow:
    def test_getters(self, mcd):
        assert isinstance(mcd.vow.vat, Vat)
        assert isinstance(mcd.vow.live(), bool)
        assert isinstance(mcd.vow.flopper(), Address)
        assert isinstance(mcd.vow.flopper(), Address)
        assert isinstance(mcd.vow.sin(), Rad)
        assert isinstance(mcd.vow.sin_of(0), Rad)
        assert isinstance(mcd.vow.ash(), Rad)
        assert isinstance(mcd.vow.woe(), Rad)
        assert isinstance(mcd.vow.wait(), int)
        assert isinstance(mcd.vow.dump(), Wad)
        assert isinstance(mcd.vow.sump(), Rad)
        assert isinstance(mcd.vow.bump(), Rad)
        assert isinstance(mcd.vow.hump(), Rad)

    def test_empty_flog(self, mcd):
        assert mcd.vow.flog(0).transact()

    def test_heal(self, mcd):
        assert mcd.vow.heal(Rad(0)).transact()

    def test_kiss(self, mcd):
        assert mcd.vow.kiss(Rad(0)).transact()


class TestJug:
    def test_getters(self, mcd, our_address):
        c = mcd.collaterals['ETH-A']
        assert isinstance(mcd.jug.vat, Vat)
        assert isinstance(mcd.jug.vow, Vow)
        assert isinstance(mcd.jug.base(), Ray)
        assert isinstance(mcd.jug.duty(c.ilk), Ray)
        assert isinstance(mcd.jug.rho(c.ilk), int)
        assert not mcd.jug.wards(our_address)

    def test_drip(self, mcd):
        # given
        c = mcd.collaterals['ETH-A']

        # then
        rho_before = mcd.jug.rho(c.ilk)
        assert rho_before > 0
        assert mcd.jug.drip(c.ilk).transact()
        rho_after = mcd.jug.rho(c.ilk)
        assert rho_before < rho_after


class TestPot:
    def setup_class(self):
        self.test_started = int(time.time())

    def test_getters(self, mcd):
        assert isinstance(mcd.pot.pie(), Wad)
        assert isinstance(mcd.pot.dsr(), Ray)
        assert isinstance(mcd.pot.rho(), int)

        assert mcd.pot.pie() >= Wad(0)
        assert mcd.pot.dsr() > Ray.from_number(1)
        assert 0 < mcd.pot.rho() < self.test_started

    def test_drip(self, mcd):
        chi_before = mcd.pot.chi()
        assert isinstance(chi_before, Ray)
        time.sleep(1)
        assert mcd.pot.drip().transact()
        time.sleep(1)
        chi_after = mcd.pot.chi()
        if mcd.pot.dsr() == Ray.from_number(1):
            assert chi_before == chi_after
        else:
            assert chi_before < chi_after
        assert self.test_started < mcd.pot.rho() < int(time.time())


class TestOsm:
    def test_price(self, web3, mcd):
        collateral = mcd.collaterals['ETH-B']
        set_collateral_price(mcd, collateral, Wad.from_number(200))
        # Note this isn't actually an OSM, but we can still read storage slots
        osm = OSM(web3, collateral.pip.address)
        raw_price = osm._extract_price(2)
        assert isinstance(raw_price, int)
        assert Wad.from_number(200) == Wad(raw_price)


class TestMcd:
    def test_healthy_cdp(self, mcd, our_address):
        collateral = mcd.collaterals['ETH-B']
        ilk = collateral.ilk
        TestVat.ensure_clean_urn(mcd, collateral, our_address)
        initial_dai = mcd.vat.dai(our_address)
        wrap_eth(mcd, our_address, Wad.from_number(9))

        # Ensure our collateral enters the urn
        collateral_balance_before = collateral.gem.balance_of(our_address)
        collateral.approve(our_address)
        assert collateral.adapter.join(our_address, Wad.from_number(9)).transact()
        assert collateral.gem.balance_of(our_address) == collateral_balance_before - Wad.from_number(9)

        # Add collateral without generating Dai
        frob(mcd, collateral, our_address, dink=Wad.from_number(3), dart=Wad(0))
        print(f"After adding collateral:         {mcd.vat.urn(ilk, our_address)}")
        assert mcd.vat.urn(ilk, our_address).ink == Wad.from_number(3)
        assert mcd.vat.urn(ilk, our_address).art == Wad(0)
        assert mcd.vat.gem(ilk, our_address) == Wad.from_number(9) - mcd.vat.urn(ilk, our_address).ink
        assert mcd.vat.dai(our_address) == initial_dai

        # Generate some Dai
        frob(mcd, collateral, our_address, dink=Wad(0), dart=Wad.from_number(153))
        print(f"After generating dai:            {mcd.vat.urn(ilk, our_address)}")
        assert mcd.vat.urn(ilk, our_address).ink == Wad.from_number(3)
        assert mcd.vat.urn(ilk, our_address).art == Wad.from_number(153)
        assert mcd.vat.dai(our_address) == initial_dai + Rad.from_number(153)

        # Add collateral and generate some more Dai
        frob(mcd, collateral, our_address, dink=Wad.from_number(6), dart=Wad.from_number(180))
        print(f"After adding collateral and dai: {mcd.vat.urn(ilk, our_address)}")
        assert mcd.vat.urn(ilk, our_address).ink == Wad.from_number(9)
        assert mcd.vat.gem(ilk, our_address) == Wad(0)
        assert mcd.vat.urn(ilk, our_address).art == Wad.from_number(333)
        assert mcd.vat.dai(our_address) == initial_dai + Rad.from_number(333)

        # Mint and withdraw our Dai
        dai_balance_before = mcd.dai.balance_of(our_address)
        mcd.approve_dai(our_address)
        assert isinstance(mcd.dai_adapter, DaiJoin)
        assert mcd.dai_adapter.exit(our_address, Wad.from_number(333)).transact()
        assert mcd.dai.balance_of(our_address) == dai_balance_before + Wad.from_number(333)
        assert mcd.vat.dai(our_address) == initial_dai
        assert mcd.vat.debt() >= initial_dai + Rad.from_number(333)

        # Repay (and burn) our Dai
        assert mcd.dai_adapter.join(our_address, Wad.from_number(333)).transact()
        assert mcd.dai.balance_of(our_address) == Wad(0)
        assert mcd.vat.dai(our_address) == initial_dai + Rad.from_number(333)
        wipe = mcd.vat.get_wipe_all_dart(collateral.ilk, our_address)
        assert wipe >= Wad.from_number(333)
        frob(mcd, collateral, our_address, dink=Wad(0), dart=wipe*-1)

        # Withdraw our collateral
        frob(mcd, collateral, our_address, dink=Wad.from_number(-9), dart=Wad(0))
        assert mcd.vat.gem(ilk, our_address) == Wad.from_number(9)
        assert collateral.adapter.exit(our_address, Wad.from_number(9)).transact()
        collateral_balance_after = collateral.gem.balance_of(our_address)
        assert collateral_balance_before == collateral_balance_after

        # Cleanup
        cleanup_urn(mcd, collateral, our_address)

    @pytest.mark.skip("awaiting change to dss-deploy-scripts allowing faucets to be enabled on local testnet")
    def test_faucet(self, mcd, our_address):
        token = mcd.collaterals['GUSD-A'].gem
        balance_before = token.balance_of(our_address)
        assert mcd.faucet.gulp(token.address).transact(from_address=our_address)
        balance_after = token.balance_of(our_address)
        assert balance_before < balance_after

    def test_empty_auctions_collection(self, mcd):
        for auction_type, collection in mcd.active_auctions().items():
            assert collection is not None
            if auction_type in ['flaps', 'flops']:
                assert len(collection) == 0
            elif auction_type in ['clips', 'flips']:
                assert len(collection) > 0
                for collateral, collateral_auctions in collection.items():
                    assert isinstance(collateral, str)
                    assert collateral_auctions is not None
                    assert len(collateral_auctions) == 0
