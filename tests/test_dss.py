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
from web3 import Web3
from web3.utils.events import get_event_data

from pymaker import Address
from pymaker.approval import hope_directly
from pymaker.deployment import DssDeployment
from pymaker.dss import Vat, Vow, Cat, Ilk, Urn, Jug, GemAdapter, DaiJoin, Spotter, Collateral
from pymaker.feed import DSValue
from pymaker.numeric import Wad, Ray, Rad
from pymaker.token import DSToken, DSEthToken


@pytest.fixture
def urn(our_address: Address, mcd: DssDeployment):
    collateral = mcd.collaterals[0]
    return mcd.vat.urn(collateral.ilk, our_address)


def wrap_eth(mcd: DssDeployment, address: Address, amount: Wad):
    assert isinstance(mcd, DssDeployment)
    assert isinstance(address, Address)
    assert isinstance(amount, Wad)
    assert amount > Wad(0)

    collateral = [c for c in mcd.collaterals if c.gem.symbol() == "WETH"][0]
    assert isinstance(collateral.gem, DSEthToken)
    assert collateral.gem.deposit(amount).transact(from_address=address)


def mint_mkr(mkr: DSToken, deployment_address: Address, recipient_address: Address, amount: Wad):
    assert isinstance(mkr, DSToken)
    assert isinstance(deployment_address, Address)
    assert isinstance(recipient_address, Address)
    assert isinstance(amount, Wad)
    assert amount > Wad(0)

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


def wait(mcd: DssDeployment, address: Address, seconds: int):
    assert isinstance(mcd, DssDeployment)
    assert isinstance(address, Address)
    assert seconds > 0

    time.sleep(5)
    # Mine a block to increment block.timestamp
    wrap_eth(mcd, address, Wad(1))


@pytest.fixture(scope="session")
def bite(web3: Web3, mcd: DssDeployment, our_address: Address):
    collateral = mcd.collaterals[0]

    # Add collateral to our CDP
    dink = Wad.from_number(1)
    wrap_eth(mcd, our_address, dink)
    assert collateral.gem.balance_of(our_address) >= dink
    assert collateral.adapter.join(our_address, dink).transact()
    TestVat.frob(mcd, collateral, our_address, dink, Wad(0))

    # Define required bite parameters
    to_price = Wad(Web3.toInt(collateral.pip.read())) / Wad.from_number(2)

    # Manipulate price to make our CDP underwater
    # Note this will only work on a testchain deployed with fixed prices, where PIP is a DSValue
    TestVat.frob(mcd, collateral, our_address, Wad(0), TestVat.max_dart(mcd, collateral, our_address))
    set_collateral_price(mcd, collateral, to_price)

    # Bite the CDP
    TestCat.simulate_bite(mcd, collateral, our_address)
    assert mcd.cat.bite(collateral.ilk, Urn(our_address)).transact()


@pytest.fixture(scope="session")
def bite_event(web3: Web3, mcd: DssDeployment, our_address: Address):
    bite(web3, mcd, our_address)
    # Return the corresponding event
    return mcd.cat.past_bite(1)[0]


class TestConfig:
    def test_from_json(self, web3: Web3, mcd: DssDeployment):
        # fixture calls DssDeployment.from_json
        assert len(mcd.config.collaterals) > 1
        assert len(mcd.collaterals) > 1
        assert len(mcd.config.to_dict()) > 10
        assert len(mcd.collaterals) == len(mcd.config.collaterals)

    def test_to_json(self, web3: Web3, mcd: DssDeployment):
        config_out = mcd.to_json()
        dict = json.loads(config_out)
        assert "MCD_GOV" in dict
        assert "MCD_DAI" in dict
        assert len(dict) > 20

    def test_account_transfers(self, web3: Web3, mcd, our_address, other_address):
        collateral = [c for c in mcd.collaterals if c.gem.symbol() == "WETH"][0]
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
    def max_dart(mcd: DssDeployment, collateral: Collateral, our_address: Address) -> Wad:
        assert isinstance(mcd, DssDeployment)
        assert isinstance(collateral, Collateral)
        assert isinstance(our_address, Address)

        urn = mcd.vat.urn(collateral.ilk, our_address)
        ilk = mcd.vat.ilk(collateral.ilk.name)

        # change in debt = (collateral balance * collateral price with safety margin) - CDP's stablecoin debt
        dart = urn.ink * ilk.spot - urn.art

        # prevent the change in debt from exceeding the collateral debt ceiling
        if (Rad(urn.art) + Rad(dart)) >= ilk.line:
            dart = Wad(ilk.line - Rad(urn.art))

        # prevent the change in debt from exceeding the total debt ceiling
        debt = mcd.vat.debt() + Rad(ilk.rate * dart)
        line = Rad(ilk.line)
        if (debt + Rad(dart)) >= line:
            dart = Wad(debt - Rad(urn.art))

        assert dart > Wad(0)
        return dart

    @staticmethod
    def simulate_frob(mcd: DssDeployment, collateral: Collateral, address: Address, dink: Wad, dart: Wad):
        assert isinstance(mcd, DssDeployment)
        assert isinstance(collateral, Collateral)
        assert isinstance(address, Address)
        assert isinstance(dink, Wad)
        assert isinstance(dart, Wad)

        urn = mcd.vat.urn(collateral.ilk, address)
        ilk = mcd.vat.ilk(collateral.ilk.name)

        print(f"urn.ink={urn.ink}, urn.art={urn.art}, ilk.art={ilk.art}, dink={dink}, dart={dart}")
        ink = urn.ink + dink
        art = urn.art + dart
        ilk_art = ilk.art + dart
        rate = ilk.rate

        gem = mcd.vat.gem(collateral.ilk, urn.address) - dink
        dai = mcd.vat.dai(urn.address) + Rad(rate * dart)
        debt = mcd.vat.debt() + Rad(rate * dart)

        # stablecoin debt does not increase
        cool = dart <= Wad(0)
        # collateral balance does not decrease
        firm = dink >= Wad(0)
        nice = cool and firm

        # CDP remains under both collateral and total debt ceilings
        under_collateral_debt_ceiling = Rad(ilk_art * rate) <= ilk.line
        if not under_collateral_debt_ceiling:
            print(f"CDP would exceed collateral debt ceiling of {ilk.line}")
        under_total_debt_ceiling = debt < ilk.line
        if not under_total_debt_ceiling:
            print(f"CDP would exceed total debt ceiling of {ilk.line}")
        calm = under_collateral_debt_ceiling and under_total_debt_ceiling

        safe = (urn.art * rate) <= ink * ilk.spot

        assert calm or cool
        assert nice or safe

        assert Rad(ilk_art * rate) >= ilk.dust or (art == Wad(0))
        assert rate != Ray(0)
        assert mcd.vat.live()

    @staticmethod
    def frob(mcd: DssDeployment, collateral: Collateral, address: Address, dink: Wad, dart: Wad):
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
        TestVat.simulate_frob(mcd, collateral, address, dink, dart)

        # then
        assert mcd.vat.frob(ilk=ilk, address=address, dink=dink, dart=dart).transact(from_address=address)
        assert mcd.vat.urn(ilk, address).ink == ink_before + dink
        assert mcd.vat.urn(ilk, address).art == art_before + dart

    @staticmethod
    def ensure_clean_urn(mcd: DssDeployment, collateral: Collateral, address: Address):
        assert isinstance(mcd, DssDeployment)
        assert isinstance(collateral, Collateral)
        assert isinstance(address, Address)

        urn = mcd.vat.urn(collateral.ilk, address)
        assert urn.ink == Wad(0)
        assert urn.art == Wad(0)
        assert mcd.vat.dai(address) == Rad(0)
        assert mcd.vat.gem(collateral.ilk, address) == Wad(0)

    @staticmethod
    def cleanup_urn(mcd: DssDeployment, collateral: Collateral, address: Address):
        assert isinstance(mcd, DssDeployment)
        assert isinstance(collateral, Collateral)
        assert isinstance(address, Address)
        urn = mcd.vat.urn(collateral.ilk, address)

        # Repay borrowed Dai
        if mcd.dai.balance_of(address) >= urn.art:
            assert mcd.dai_adapter.join(address, urn.art).transact(from_address=address)
        TestVat.frob(mcd, collateral, address, Wad(0), urn.art * -1)

        # Withdraw collateral
        TestVat.frob(mcd, collateral, address, urn.ink * -1, Wad(0))
        assert collateral.adapter.exit(address, mcd.vat.gem(collateral.ilk, address)).transact(from_address=address)

        TestVat.ensure_clean_urn(mcd, collateral, address)

    def test_getters(self, mcd):
        assert isinstance(mcd.vat.live(), bool)

    def test_ilk(self, mcd):
        assert mcd.vat.ilk('XXX') == Ilk('XXX',
                                         rate=Ray(0), ink=Wad(0), art=Wad(0), spot=Ray(0), line=Rad(0), dust=Rad(0))

    def test_gem(self, web3: Web3, mcd: DssDeployment, our_address: Address):
        # given
        collateral = mcd.collaterals[0]
        amount_to_join = Wad(10)
        our_urn = mcd.vat.urn(collateral.ilk, our_address)
        assert isinstance(collateral.ilk, Ilk)
        assert isinstance(collateral.adapter, GemAdapter)
        assert collateral.ilk == collateral.adapter.ilk()
        assert our_urn.address == our_address
        wrap_eth(mcd, our_address, amount_to_join)
        assert collateral.gem.balance_of(our_address) >= amount_to_join

        # when
        before_join = mcd.vat.gem(collateral.ilk, our_urn.address)
        assert collateral.adapter.join(our_address, amount_to_join).transact()
        after_join = mcd.vat.gem(collateral.ilk, our_urn.address)
        assert collateral.adapter.exit(our_address, amount_to_join).transact()
        after_exit = mcd.vat.gem(collateral.ilk, our_urn.address)

        # then
        assert after_join - before_join == amount_to_join
        assert after_exit == before_join

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

    def test_frob_noop(self, mcd, our_address):
        # given
        collateral = mcd.collaterals[0]
        our_urn = mcd.vat.urn(collateral.ilk, our_address)

        # when
        assert mcd.vat.frob(collateral.ilk, our_address, Wad(0), Wad(0)).transact()

        # then
        assert mcd.vat.urn(collateral.ilk, our_address) == our_urn

    def test_frob_add_ink(self, mcd, our_address):
        # given
        collateral = mcd.collaterals[0]
        our_urn = mcd.vat.urn(collateral.ilk, our_address)

        # when
        wrap_eth(mcd, our_address, Wad(10))
        assert collateral.adapter.join(our_address, Wad(10)).transact()
        assert mcd.vat.frob(collateral.ilk, our_address, Wad(10), Wad(0)).transact()

        # then
        assert mcd.vat.urn(collateral.ilk, our_address).ink == our_urn.ink + Wad(10)

        # rollback
        self.cleanup_urn(mcd, collateral, our_address)

    def test_frob_add_art(self, mcd, our_address: Address):
        # given
        collateral = mcd.collaterals[0]
        our_urn = mcd.vat.urn(collateral.ilk, our_address)

        # when
        wrap_eth(mcd, our_address, Wad(10))
        assert collateral.adapter.join(our_address, Wad(3)).transact()
        assert mcd.vat.frob(collateral.ilk, our_address, Wad(3), Wad(10)).transact()

        # then
        assert mcd.vat.urn(collateral.ilk, our_address).art == our_urn.art + Wad(10)

        # rollback
        self.cleanup_urn(mcd, collateral, our_address)

    def test_frob_other_account(self, web3, mcd, other_address):
        # given
        collateral = mcd.collaterals[0]
        urn = mcd.vat.urn(collateral.ilk, other_address)
        assert urn.address == other_address

        # when
        wrap_eth(mcd, other_address, Wad(10))
        assert collateral.gem.balance_of(other_address) >= Wad(10)
        assert collateral.gem == collateral.adapter.gem()
        collateral.gem.approve(collateral.adapter.address)
        assert collateral.adapter.join(other_address, Wad(3)).transact(from_address=other_address)
        assert mcd.vat.frob(collateral.ilk, other_address, Wad(3), Wad(10)).transact(from_address=other_address)

        # then
        assert mcd.vat.urn(collateral.ilk, other_address).art == urn.art + Wad(10)

        # rollback
        self.cleanup_urn(mcd, collateral, other_address)

    def test_heal(self, mcd):
        assert mcd.vat.heal(Rad(0))

    def test_suck(self, mcd, our_address):
        assert mcd.vat.suck(our_address, our_address, Rad(0))

    @pytest.mark.skip(reason="Using TestVatLogs class to establish a working implementation")
    def test_past_note(self, our_address, mcd):
        # given
        c = mcd.collaterals[0]

        # when
        assert mcd.vat.frob(c.ilk, our_address, Wad(0), Wad(0)).transact()

        # then
        #last_frob_event = mcd.vat.past_note(1, event_filter={'ilk': c.ilk.toBytes()})[-1]
        frob_events = mcd.vat.past_note(100)
        print(frob_events)
        assert len(frob_events) > 0
        last_frob_event = frob_events[-1]
        assert last_frob_event.ilk == c.ilk
        # assert last_frob_event.dink == Wad(0)
        # assert last_frob_event.dart == Wad(0)
        # assert last_frob_event.urn.address == our_address


class TestVatLogs:
    def test_get_filter_topics(self, web3: Web3, our_address, mcd):
        changes = self.get_filter_changes(web3, our_address, mcd)
        topics = changes[0]['topics']
        print(f"event topics: {topics}")
        assert len(topics) > 0
        # event topics: [
        # HexBytes('0x7608870300000000000000000000000000000000000000000000000000000000'),
        # HexBytes('0x4554482d41000000000000000000000000000000000000000000000000000000'),
        # HexBytes('0x00000000000000000000000050ff810797f75f6bfbf2227442e0c961a8562f4c'),
        # HexBytes('0x00000000000000000000000050ff810797f75f6bfbf2227442e0c961a8562f4c')]

    def get_filter_changes(self, web3: Web3, our_address, d: DssDeployment):
        # attach filter before taking an action
        vat_filter = web3.eth.filter({'address': str(d.vat.address.address)})

        # do something with the contract
        c = d.collaterals[0]
        assert d.vat.frob(c.ilk, our_address, Wad(0), Wad(0)).transact()

        # examine event topics; note this method empties the list!
        # block_number = web3.eth.blockNumber
        # number_of_past_blocks = 10
        # event_filter = None
        # vat_filter = d.vat._contract.events['LogNote'].createFilter(fromBlock=max(block_number - number_of_past_blocks, 0),
        #                                              toBlock=block_number,
        #                                              argument_filters=event_filter)

        # FIXME: When filtering previous blocks, no events are found.
        # But when setting up a filter before frobbing, events are produced.
        return vat_filter.get_all_entries()    # _past_events uses this
        #return web3.eth.getFilterChanges(vat_filter.filter_id)

    def test_vat_events(self, web3: Web3, our_address, mcd):
        events = mcd.vat._contract.events.__dict__["_events"]
        print(f"vat events: {events}")
        assert len(events) > 0

        log_frob_abi = [abi for abi in Vat.abi if abi.get('name') == 'LogNote'][0]

        log_entries = self.get_filter_changes(web3, our_address, mcd)
        assert len(log_entries) > 0
        for event in log_entries:
            event_data = get_event_data(log_frob_abi, event)
            log_note = Vat.LogFrob.from_event(event)
            print(f'log note: {log_note}')


class TestCat:
    @staticmethod
    def simulate_bite(mcd: DssDeployment, collateral: Collateral, our_address: Address):
        assert isinstance(mcd, DssDeployment)
        assert isinstance(collateral, Collateral)
        assert isinstance(our_address, Address)

        ilk = mcd.vat.ilk(collateral.ilk.name)
        urn = mcd.vat.urn(collateral.ilk, our_address)

        # Collateral value should be less than the product of our stablecoin debt and the debt multiplier
        assert (Ray(urn.ink) * ilk.spot) < (Ray(urn.art) * ilk.rate)

        # Lesser of our collateral balance and the liquidation quantity
        lot = min(urn.ink, mcd.cat.lump(ilk))  # Wad
        # Lesser of our stablecoin debt and the canceled debt pro rata the seized collateral
        art = min(urn.art, (lot * urn.art) / urn.ink)  # Wad
        # Stablecoin to be raised in flip auction
        tab = art * ilk.rate  # Ray

        assert -int(lot) < 0 and -int(art) < 0
        assert tab > Ray(0)


    def test_getters(self, mcd):
        assert isinstance(mcd.cat.live(), bool)
        assert mcd.cat.vat() == mcd.vat.address
        assert mcd.cat.vow() == mcd.vow.address

        collateral = mcd.collaterals[2]
        assert mcd.cat.flipper(collateral.ilk) == collateral.flipper.address
        assert isinstance(mcd.cat.lump(collateral.ilk), Wad)
        assert isinstance(mcd.cat.chop(collateral.ilk), Ray)


class TestVow:
    def test_getters(self, mcd):
        assert isinstance(mcd.vow.live(), bool)
        assert isinstance(mcd.vow.flopper(), Address)
        assert isinstance(mcd.vow.flopper(), Address)
        assert isinstance(mcd.vow.sin(), Rad)
        assert isinstance(mcd.vow.sin_of(0), Rad)
        assert isinstance(mcd.vow.woe(), Rad)
        assert isinstance(mcd.vow.ash(), Rad)
        assert isinstance(mcd.vow.joy(), Rad)
        assert isinstance(mcd.vow.awe(), Rad)
        assert isinstance(mcd.vow.wait(), int)
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
    def test_getters(self, mcd):
        c = mcd.collaterals[0]
        assert isinstance(mcd.jug.vow(), Address)
        assert isinstance(mcd.jug.vat(), Address)
        assert isinstance(mcd.jug.base(), Wad)
        assert isinstance(mcd.jug.duty(c.ilk), Ray)
        assert isinstance(mcd.jug.rho(c.ilk), int)

    def test_drip(self, mcd):
        # given
        c = mcd.collaterals[0]

        # then
        assert mcd.jug.drip(c.ilk).transact()


class TestMcd:
    def test_healthy_cdp(self, web3, mcd, our_address):
        collateral = mcd.collaterals[1]
        ilk = collateral.ilk
        TestVat.ensure_clean_urn(mcd, collateral, our_address)
        wrap_eth(mcd, our_address, Wad.from_number(9))

        # Ensure our collateral enters the urn
        collateral_balance_before = collateral.gem.balance_of(our_address)
        assert collateral.adapter.join(our_address, Wad.from_number(9)).transact()
        assert collateral.gem.balance_of(our_address) == collateral_balance_before - Wad.from_number(9)

        # Add collateral without generating Dai
        TestVat.frob(mcd, collateral, our_address, dink=Wad.from_number(3), dart=Wad(0))
        print(f"After adding collateral:         {mcd.vat.urn(ilk, our_address)}")
        assert mcd.vat.urn(ilk, our_address).ink == Wad.from_number(3)
        assert mcd.vat.urn(ilk, our_address).art == Wad(0)
        assert mcd.vat.gem(ilk, our_address) == Wad.from_number(9) - mcd.vat.urn(ilk, our_address).ink
        assert mcd.vat.dai(our_address) == Rad(0)

        # Generate some Dai
        TestVat.frob(mcd, collateral, our_address, dink=Wad(0), dart=Wad.from_number(153))
        print(f"After generating dai:            {mcd.vat.urn(ilk, our_address)}")
        assert mcd.vat.urn(ilk, our_address).ink == Wad.from_number(3)
        assert mcd.vat.urn(ilk, our_address).art == Wad.from_number(153)
        assert mcd.vat.dai(our_address) == Rad.from_number(153)

        # Add collateral and generate some more Dai
        TestVat.frob(mcd, collateral, our_address, dink=Wad.from_number(6), dart=Wad.from_number(180))
        print(f"After adding collateral and dai: {mcd.vat.urn(ilk, our_address)}")
        assert mcd.vat.urn(ilk, our_address).ink == Wad.from_number(9)
        assert mcd.vat.gem(ilk, our_address) == Wad(0)
        assert mcd.vat.urn(ilk, our_address).art == Wad.from_number(333)
        assert mcd.vat.dai(our_address) == Rad.from_number(333)

        # Mint and withdraw our Dai
        dai_balance_before = mcd.dai.balance_of(our_address)
        assert isinstance(mcd.dai_adapter, DaiJoin)
        # Ensure vat permissions are set up for our account
        assert mcd.vat.can(our_address, mcd.dai_adapter.address)
        assert mcd.dai_adapter.exit(our_address, Wad.from_number(333)).transact()
        assert mcd.dai.balance_of(our_address) == dai_balance_before + Wad.from_number(333)
        assert mcd.vat.dai(our_address) == Rad(0)

        # Repay (and burn) our Dai
        assert mcd.dai_adapter.join(our_address, Wad.from_number(333)).transact()
        assert mcd.dai.balance_of(our_address) == Wad(0)
        assert mcd.vat.dai(our_address) == Rad.from_number(333)

        # Withdraw our collateral
        TestVat.frob(mcd, collateral, our_address, dink=Wad(0), dart=Wad.from_number(-333))
        TestVat.frob(mcd, collateral, our_address, dink=Wad.from_number(-9), dart=Wad(0))
        assert mcd.vat.gem(ilk, our_address) == Wad.from_number(9)
        assert collateral.adapter.exit(our_address, Wad.from_number(9)).transact()
        collateral_balance_after = collateral.gem.balance_of(our_address)
        assert collateral_balance_before == collateral_balance_after

        # Cleanup
        TestVat.cleanup_urn(mcd, collateral, our_address)