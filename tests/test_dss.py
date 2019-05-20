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

import eth_abi
import json
import logging
import pytest
from eth_utils import decode_hex
from hexbytes import HexBytes
from web3 import Web3, HTTPProvider
from web3.utils.events import get_event_data

from pymaker import Address
from pymaker.auctions import Flipper, Flapper, Flopper
from pymaker.deployment import DssDeployment
from pymaker.dss import Vat, Vow, Cat, Ilk, Urn, Jug, GemAdapter, Spotter
from pymaker.feed import DSValue
from pymaker.keys import register_keys
from pymaker.numeric import Ray, Wad, Rad
from pymaker.token import DSToken


@pytest.fixture(scope="session")
def web3():
    # for ganache
    # web3 = Web3(HTTPProvider("http://localhost:8555"))
    # web3.eth.defaultAccount = web3.eth.accounts[0]

    # for Kovan
    # web3 = Web3(HTTPProvider(endpoint_uri="https://parity0.kovan.makerfoundation.com:8545",
    #                          request_kwargs={"timeout": 10}))
    # web3.eth.defaultAccount = "0xC140ce1be1c0edA2f06319d984c404251C59494e"
    # register_keys(web3,
    #               ["key_file=/home/ed/Projects/member-account.json,pass_file=/home/ed/Projects/member-account.pass",
    #                "key_file=/home/ed/Projects/kovan-account2.json,pass_file=/home/ed/Projects/kovan-account2.pass"])

    # for local dockerized parity testchain
    web3 = Web3(HTTPProvider("http://0.0.0.0:8545"))
    web3.eth.defaultAccount = "0x50FF810797f75f6bfbf2227442e0c961a8562F4C"
    register_keys(web3,
                  ["key_file=tests/config/keys/UnlimitedChain/key1.json,pass_file=/dev/null",
                   "key_file=tests/config/keys/UnlimitedChain/key2.json,pass_file=/dev/null"])

    logging.getLogger("web3").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.INFO)

    assert len(web3.eth.accounts) > 1
    return web3


@pytest.fixture(scope="session")
def other_address(web3):
    return Address(web3.eth.accounts[1])


@pytest.fixture(scope="session")
def our_address(web3):
    return Address(web3.eth.accounts[0])


@pytest.fixture(scope="session")
def d(web3):
    # Deploy through pymaker
    #deployment = DssDeployment.deploy(web3=web3)

    # Use an existing deployment
    # deployment = DssDeployment.from_json(web3=web3,
    #                                      conf=open("tests/config/kovan-addresses.json", "r").read())
    deployment = DssDeployment.from_json(web3=web3,
                                         conf=open("/home/ed/Projects/parity-fixed-addresses.json", "r").read())

    assert isinstance(deployment.vat, Vat)
    assert deployment.vat.address is not None
    assert isinstance(deployment.vow, Vow)
    assert deployment.vow.address is not None
    assert isinstance(deployment.cat, Cat)
    assert deployment.cat.address is not None
    assert isinstance(deployment.jug, Jug)
    assert deployment.jug.address is not None
    assert isinstance(deployment.flap, Flapper)
    assert deployment.flap.address is not None
    assert isinstance(deployment.flop, Flopper)
    assert deployment.flop.address is not None

    # for c in deployment.collaterals:
    #     assert c.gem.mint(Wad.from_number(1000)).transact()
    return deployment


@pytest.fixture(scope="session")
def bite(our_address: Address, d: DssDeployment):
    collateral = d.collaterals[0]

    # Add collateral to our CDP
    assert collateral.adapter.join(Urn(our_address), Wad.from_number(1)).transact()
    assert d.vat.frob(ilk=collateral.ilk, address=our_address, dink=Wad.from_number(1), dart=Wad(0)).transact()

    # Define required bite parameters
    our_urn = d.vat.urn(collateral.ilk, our_address)
    max_dart = our_urn.ink * d.vat.spot(collateral.ilk) - our_urn.art
    to_price = Wad(Web3.toInt(collateral.pip.read())) - Wad.from_number(1)

    # Manipulate price to make our CDP underwater
    # Note this will only work on a testchain deployed with fixed prices, where PIP is a DSValue
    assert d.vat.frob(ilk=collateral.ilk, address=our_address, dink=Wad(0), dart=max_dart).transact()
    assert collateral.pip.poke_with_int(to_price.value).transact()
    assert d.spotter.poke(ilk=collateral.ilk).transact()

    # Bite the CDP
    assert d.cat.bite(collateral.ilk, Urn(our_address)).transact()


@pytest.fixture(scope="session")
def bite_event(our_address: Address, d: DssDeployment):
    bite(our_address, d)
    # Return the corresponding event
    return d.cat.past_bite(1)[0]


class TestConfig:
    def test_from_json(self, web3: Web3, d: DssDeployment):
        # fixture calls DssDeployment.from_json
        assert len(d.config.collaterals) > 1
        assert len(d.collaterals) > 1
        assert len(d.config.to_dict()) > 10
        assert len(d.collaterals) == len(d.config.collaterals)

    def test_to_json(self, web3: Web3, d: DssDeployment):
        config_out = d.to_json()
        dict = json.loads(config_out)
        assert "MCD_GOV" in dict
        assert "MCD_DAI" in dict
        assert len(dict) > 20

    def test_account_transfers(self, web3: Web3, d: DssDeployment, our_address, other_address):
        collateral = d.collaterals[0]
        token = collateral.gem
        assert isinstance(token, DSToken)
        amount = Wad(10)

        assert web3.eth.defaultAccount == our_address.address
        assert our_address != other_address

        # Move eth between each account to confirm keys are properly set up
        before = token.balance_of(our_address)
        assert token.transfer_from(our_address, other_address, amount).transact()
        web3.eth.defaultAccount = other_address.address  # Unsure why this is necessary
        after = token.balance_of(our_address)
        assert (before - amount) == after
        assert token.transfer_from(other_address, our_address, amount).transact()
        assert token.balance_of(our_address) == before

        web3.eth.defaultAccount = our_address


class TestVat:
    """ `Vat` class testing """

    def test_rely(self, d: DssDeployment, other_address: Address):
        # when
        assert d.vat.rely(other_address).transact()

        # then
        assert d.vat.init(Ilk('ETH')).transact(from_address=other_address)

    def test_ilk(self, d: DssDeployment):
        assert d.vat.ilk('XXX') == Ilk('XXX', rate=Ray(0), ink=Wad(0), art=Wad(0))

    def test_gem(self, our_address: Address, d: DssDeployment):
        # given
        collateral = d.collaterals[0]
        amount_to_join = Wad(10)
        our_urn = d.vat.urn(collateral.ilk, our_address)
        assert isinstance(collateral.ilk, Ilk)
        assert isinstance(collateral.gem, DSToken)
        assert isinstance(collateral.adapter, GemAdapter)
        assert collateral.ilk == collateral.adapter.ilk()
        assert our_urn.address == our_address
        # If this fails, you need to wrap more ETH
        assert collateral.gem.balance_of(our_address) > amount_to_join

        # when
        before_join = d.vat.gem(collateral.ilk, our_urn.address)
        assert collateral.adapter.join(our_urn, amount_to_join).transact()
        after_join = d.vat.gem(collateral.ilk, our_urn.address)
        assert collateral.adapter.exit(our_urn, amount_to_join).transact()
        after_exit = d.vat.gem(collateral.ilk, our_urn.address)

        # then
        assert after_join - before_join == amount_to_join
        assert after_exit == before_join

    def test_frob_noop(self, d: DssDeployment, our_address: Address):
        # given
        collateral = d.collaterals[0]
        our_urn = d.vat.urn(collateral.ilk, our_address)

        # when
        assert d.vat.frob(collateral.ilk, our_address, Wad(0), Wad(0)).transact()

        # then
        assert d.vat.urn(collateral.ilk, our_address) == our_urn

    def test_frob_add_ink(self, d: DssDeployment, our_address: Address):
        # given
        collateral = d.collaterals[0]
        our_urn = d.vat.urn(collateral.ilk, our_address)

        # when
        assert collateral.adapter.join(our_urn, Wad(10)).transact()
        assert d.vat.frob(collateral.ilk, our_address, Wad(10), Wad(0)).transact()

        # then
        assert d.vat.urn(collateral.ilk, our_address).ink == our_urn.ink + Wad(10)

    def test_frob_add_art(self, d: DssDeployment, our_address: Address):
        # given
        collateral = d.collaterals[0]
        our_urn = d.vat.urn(collateral.ilk, our_address)

        # when
        assert collateral.adapter.join(our_urn, Wad(10)).transact()
        assert d.vat.frob(collateral.ilk, our_address, Wad(0), Wad(10)).transact()

        # then
        assert d.vat.urn(collateral.ilk, our_address).art == our_urn.art + Wad(10)

    @pytest.mark.skip(reason="Using TestVatLogs class to establish a working implementation")
    def test_past_note(self, our_address, d: DssDeployment):
        # given
        c = d.collaterals[0]

        # when
        assert d.vat.frob(c.ilk, our_address, Wad(0), Wad(0)).transact()

        # then
        last_frob_event = d.vat.past_note(1, event_filter={'ilk': c.ilk.toBytes()})[-1]
        assert last_frob_event.ilk == c.ilk
        assert last_frob_event.dink == Wad(0)
        assert last_frob_event.dart == Wad(0)
        assert last_frob_event.urn.address == our_address


class TestVatLogs:
    def test_get_filter_topics(self, web3: Web3, our_address, d: DssDeployment):
        changes = self.get_filter_changes(web3, our_address, d)
        topics = changes[0]['topics']
        print(f"event topics: {topics}")
        assert len(topics) > 0

    def get_filter_changes(self, web3: Web3, our_address, d: DssDeployment):
        # attach filter before taking an action
        vat_filter = web3.eth.filter({'address': str(d.vat.address.address)})

        # do something with the contract
        c = d.collaterals[0]
        assert d.vat.frob(c.ilk, our_address, Wad(0), Wad(0)).transact()

        # examine event topics; note this method empties the list!
        return web3.eth.getFilterChanges(vat_filter.filter_id)

    def test_vat_events(self, web3: Web3, our_address, d: DssDeployment):
        events = d.vat._contract.events.__dict__["_events"]
        print(f"vat events: {events}")
        assert len(events) > 0

        log_frob_abi = [abi for abi in Vat.abi if abi.get('name') == 'LogNote'][0]
        log_entry = self.get_filter_changes(web3, our_address, d)[0]  # d.vat._contract.events.LogNote()
        # TODO: Consider writing a custom decode method to handle Vat's anonymous event
        print(log_entry['data'])

        event_data = get_event_data(log_frob_abi, log_entry)
        print(event_data)


class TestCat:
    def test_empty_flips(self, d: DssDeployment):
        nflip = d.cat.nflip()
        assert d.cat.flips(nflip + 1) == Cat.Flip(nflip + 1,
                                                  Urn(address=Address('0x0000000000000000000000000000000000000000')),
                                                  Wad(0))

    def test_bite(self, our_address, d: DssDeployment):
        # given
        collateral = d.collaterals[0]
        assert collateral.adapter.join(Urn(our_address), Wad.from_number(2)).transact()
        assert d.vat.frob(ilk=collateral.ilk, address=our_address, dink=Wad.from_number(2), dart=Wad(0)).transact()
        our_urn = d.vat.urn(collateral.ilk, our_address)
        max_dart = our_urn.ink * d.vat.spot(collateral.ilk) - our_urn.art
        to_price = Wad(Web3.toInt(collateral.pip.read())) - Wad.from_number(10)

        # when
        assert d.vat.frob(ilk=collateral.ilk, address=our_address, dink=Wad(0), dart=max_dart).transact()
        assert collateral.pip.poke_with_int(to_price.value).transact()
        assert d.spotter.poke(ilk=collateral.ilk).transact()

        # then
        assert d.cat.bite(collateral.ilk, Urn(our_address)).transact()

    @pytest.mark.skip(reason="bite_event moved to TestCatLogs for diagnosis")
    def test_past_bite(self, d: DssDeployment, bite_event):
        assert d.cat.past_bite(1) == [bite_event]

    def test_flip(self, web3, d: DssDeployment, bite):
        # given
        collateral = d.collaterals[0]
        nflip = d.cat.nflip()
        flipper = Flipper(web3=web3, address=d.cat.flipper(collateral.ilk))
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


class TestCatLogs:
    def test_get_filter_topics(self, web3: Web3, our_address, d: DssDeployment):
        changes = self.get_filter_changes(web3, our_address, d)
        topics = changes[0]['topics']
        print(f"event topics: {topics}")
        assert len(topics) > 0

    def get_filter_changes(self, web3: Web3, our_address: Address, d: DssDeployment):
        # attach filter before taking an action
        vat_filter = web3.eth.filter({'address': str(d.vat.address.address)})

        self.bite(our_address, d)

        # examine event topics; note this method empties the list!
        return web3.eth.getFilterChanges(vat_filter.filter_id)

    def test_event_filter(self, web3: Web3, our_address: Address, d: DssDeployment):
        events = d.cat._contract.events.__dict__["_events"]
        print(f"cat events: {events}")
        assert len(events) > 0

        types = []
        names = []
        indexed_types = []
        indexed_names = []
        for elem in Cat.abi:
            if 'name' in elem and elem['name'] == 'LogNote':
                for input in elem['inputs']:
                    if input['indexed']:
                        indexed_types.append(input["type"])
                        indexed_names.append(input["name"])
                    else:
                        types.append(input["type"])
                        names.append(input["name"])
                break

        logs = self.get_filter_changes(web3, our_address, d)
        assert len(logs) > 0
        for log in logs:
            print(f"log data {log['data']}")

        values = eth_abi.decode_abi(types, decode_hex(log['data']))
        assert len(values) > 0
        for value in values:
            print(f"value {value.hex()}")
        assert False


    @pytest.mark.skip(reason="past_events collection is always empty")
    def test_past_events(self, bite_event, d: DssDeployment):
        past_events = d.cat._past_events(d.cat._contract, 'Bite', Cat.LogBite, 1, None)
        print(past_events)
        assert len(past_events) > 0


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
        assert d.vow.flog(0).transact()

    # FIXME: This test requests Cat.LogBite to be working
    def test_flog(self, web3, d: DssDeployment, bite_event):
        # given
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

    # FIXME: Vow accounting issue needs resolution
    def test_flap(self, web3, our_address, d: DssDeployment, bite):
        # given
        c = d.collaterals[0]
        surplus_before = d.vow.awe()
        assert d.vat.frob(c.ilk, our_address, Wad(0), Wad.from_number(11000)).transact()
        art = d.vat.urn(c.ilk, our_address).art
        assert art > Wad(0)
        lump_before = d.cat.lump(c.ilk)
        sin_before = d.vow.sin()

        # Calculate lot
        lot = min(d.vat.urn(c.ilk, our_address).ink, d.cat.lump(c.ilk))
        assert lot > Wad(0)

        # Calculate art
        # min(u.art, mul(lot, u.art) / u.ink)
        urn_before_bite = d.vat.urn(c.ilk, our_address)
        print(f"VAT before bite: ink={urn_before_bite.ink}, art={urn_before_bite.art}")
        art = min(urn_before_bite.art, (lot * urn_before_bite.art) / urn_before_bite.ink)
        assert art > Wad(0)

        # Calculate tab, which is the value passed to vow.fess
        rate = d.vat.ilk(c.ilk.name).rate
        assert rate > Ray(0)
        tab = Ray(art) * rate
        assert tab > Ray(0)

        # Manipulate price to make our CDP underwater, and then bite the CDP
        to_price = Wad(Web3.toInt(c.pip.read())) / Wad.from_number(2)
        assert c.pip.poke_with_int(to_price.value).transact()
        assert d.spotter.poke(ilk=c.ilk).transact()
        print(f"CAT during bite: lot={lot}, art={art}, tab={tab}")
        assert d.cat.bite(c.ilk, Urn(our_address)).transact()

        # Log some values
        urn_after_bite = d.vat.urn(c.ilk, our_address)
        print(f"VAT after bite: ink={urn_after_bite.ink}, art={urn_after_bite.art}")
        print(f"VOW after bite: sin={d.vow.sin()}, ash={d.vow.ash()}, awe={d.vow.awe()}")

        # when
        assert d.vow.sin() >= Wad(tab)
        lump_after = d.cat.lump(c.ilk)
        assert lump_before < lump_after
        surplus_after = d.vow.awe()
        assert surplus_before < surplus_after
        assert d.vow.heal(d.vow.woe()).transact()
        assert d.vow.joy() >= (d.vow.awe() + d.vow.bump() + d.vow.hump())
        assert d.vow.woe() == Wad(0)

        # then
        assert d.vow.flap().transact()

    # FIXME: This test requests Cat.LogBite to be working
    def test_flop(self, web3, d: DssDeployment, bite):
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


class TestJug:
    def test_getters(self, d: DssDeployment):
        c = d.collaterals[0]
        assert isinstance(d.jug.vow(), Address)
        assert isinstance(d.jug.vat(), Address)
        assert isinstance(d.jug.base(), Wad)
        assert isinstance(d.jug.duty(c.ilk), Ray)
        assert isinstance(d.jug.rho(c.ilk), int)

    def test_drip(self, d: DssDeployment):
        # given
        c = d.collaterals[0]

        # then
        assert d.jug.drip(c.ilk).transact()

    def test_file_duty(self, d: DssDeployment):
        # given
        c = d.collaterals[0]

        # then
        assert d.jug.file_duty(c.ilk, Ray(1000000564701133626865910626)).transact()
