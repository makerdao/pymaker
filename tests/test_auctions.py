# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
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

from web3 import Web3, EthereumTesterProvider

from pymaker import Address, Wad, Contract
from pymaker.approval import directly
from pymaker.auctions import Flipper, Flapper, Flopper
from pymaker.auth import DSGuard
from pymaker.token import DSToken
from tests.helpers import time_travel_by


class TestFlipper:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.other_address_1 = Address(self.web3.eth.accounts[1])
        self.other_address_2 = Address(self.web3.eth.accounts[2])

        # we need VatMock to mock Vat, as Flipper won't work without it
        self.vat_address = Contract._deploy(self.web3, Contract._load_abi(__name__, 'abi/VatMock.abi'), Contract._load_bin(__name__, 'abi/VatMock.bin'), [])
        self.vat_contract = self.web3.eth.contract(abi=Contract._load_abi(__name__, 'abi/VatMock.abi'))(address=self.vat_address.address)

        self.flipper = Flipper.deploy(self.web3, self.vat_address, 123)

    def dai_balance(self, address: Address) -> Wad:
        assert(isinstance(address, Address))
        return Wad(self.vat_contract.call().dai(address.address))

    def dai_mint(self, address: Address, amount: Wad):
        assert(isinstance(address, Address))
        assert(isinstance(amount, Wad))
        self.vat_contract.transact().mint(address.address, amount.value)

    def gem_balance(self, address: Address) -> Wad:
        assert(isinstance(address, Address))
        return Wad(self.vat_contract.call().gem(address.address))

    def test_era(self):
        assert self.flipper.era() > 1000000

    def test_beg(self):
        assert self.flipper.beg() == Wad.from_number(1.05)

    def test_ttl(self):
        assert self.flipper.ttl() == 3*60*60

    def test_tau(self):
        assert self.flipper.tau() == 7*24*60*60

    def test_read(self):
        # when
        self.flipper.kick(lad=self.other_address_1,
                          gal=self.other_address_2,
                          tab=Wad.from_number(5000),
                          lot=Wad.from_number(100),
                          bid=Wad.from_number(1000)).transact()

        # then
        assert self.flipper.kicks() == 1
        # and
        auction = self.flipper.bids(1)
        assert auction.lad == self.other_address_1
        assert auction.gal == self.other_address_2
        assert auction.bid == Wad.from_number(1000)
        assert auction.lot == Wad.from_number(100)
        assert auction.tab == Wad.from_number(5000)
        assert auction.guy == self.our_address
        assert auction.tic == 0
        assert auction.end > 0

    def test_scenario(self):
        # given
        self.dai_mint(self.our_address, Wad.from_number(100000))
        assert self.dai_balance(self.our_address) == Wad.from_number(100000)

        # when
        self.flipper.kick(lad=self.other_address_1,
                          gal=self.other_address_1,
                          tab=Wad.from_number(5000),
                          lot=Wad.from_number(100),
                          bid=Wad.from_number(1000)).transact(from_address=self.other_address_1)
        # then
        assert self.dai_balance(self.our_address) == Wad.from_number(100000)
        assert self.dai_balance(self.other_address_1) == Wad.from_number(0)
        assert self.gem_balance(self.our_address) == Wad.from_number(0)
        assert self.gem_balance(self.other_address_1) == Wad.from_number(0)

        # when
        self.flipper.tend(1, Wad.from_number(100), Wad.from_number(2000)).transact()
        assert self.dai_balance(self.our_address) == Wad.from_number(100000) - Wad.from_number(2000)
        assert self.dai_balance(self.other_address_1) == Wad.from_number(2000)
        assert self.gem_balance(self.our_address) == Wad.from_number(0)
        assert self.gem_balance(self.other_address_1) == Wad.from_number(0)

        # when
        self.flipper.tend(1, Wad.from_number(100), Wad.from_number(5000)).transact()
        assert self.dai_balance(self.our_address) == Wad.from_number(100000) - Wad.from_number(5000)
        assert self.dai_balance(self.other_address_1) == Wad.from_number(5000)
        assert self.gem_balance(self.our_address) == Wad.from_number(0)
        assert self.gem_balance(self.other_address_1) == Wad.from_number(0)

        # when
        self.flipper.dent(1, Wad.from_number(80), Wad.from_number(5000)).transact()
        assert self.dai_balance(self.our_address) == Wad.from_number(100000) - Wad.from_number(5000)
        assert self.dai_balance(self.other_address_1) == Wad.from_number(5000)
        assert self.gem_balance(self.our_address) == Wad.from_number(0)
        assert self.gem_balance(self.other_address_1) == Wad.from_number(20)

        time_travel_by(self.web3, 60*60*24*8)

        # when
        self.flipper.deal(1).transact()
        assert self.dai_balance(self.our_address) == Wad.from_number(100000) - Wad.from_number(5000)
        assert self.dai_balance(self.other_address_1) == Wad.from_number(5000)
        assert self.gem_balance(self.our_address) == Wad.from_number(80)
        assert self.gem_balance(self.other_address_1) == Wad.from_number(20)


class TestFlapper:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.pie = DSToken.deploy(self.web3, 'DAI')
        self.gem = DSToken.deploy(self.web3, 'MKR')
        self.flapper = Flapper.deploy(self.web3, self.pie.address, self.gem.address)

    def test_era(self):
        assert self.flapper.era() > 1000000

    def test_pie(self):
        assert self.flapper.pie() == self.pie.address

    def test_gem(self):
        assert self.flapper.gem() == self.gem.address

    def test_beg(self):
        assert self.flapper.beg() == Wad.from_number(1.05)

    def test_ttl(self):
        assert self.flapper.ttl() == 3*60*60

    def test_tau(self):
        assert self.flapper.tau() == 7*24*60*60

    def test_read(self):
        # given
        pit = Address(self.web3.eth.accounts[1])
        # and
        self.pie.mint(Wad.from_number(50000000)).transact()
        self.gem.mint(Wad.from_number(1000)).transact()

        # expect
        assert self.flapper.kicks() == 0

        # when
        self.pie.approve(self.flapper.address).transact()
        self.flapper.kick(pit, Wad.from_number(20000), Wad.from_number(1)).transact()
        # then
        assert self.flapper.kicks() == 1
        # and
        auction = self.flapper.bids(1)
        assert auction.bid == Wad.from_number(1)
        assert auction.lot == Wad.from_number(20000)
        assert auction.guy == self.our_address
        assert auction.tic == 0
        assert auction.end > 0

    def test_scenario(self):
        # given
        pit = Address(self.web3.eth.accounts[1])
        # and
        self.pie.mint(Wad.from_number(50000000)).transact()
        self.gem.mint(Wad.from_number(1000)).transact()

        # when
        self.pie.approve(self.flapper.address).transact()
        self.flapper.kick(pit, Wad.from_number(20000), Wad.from_number(1)).transact()
        # then
        assert self.pie.balance_of(self.our_address) == Wad.from_number(49980000)
        assert self.gem.balance_of(pit) == Wad.from_number(0)
        # and
        assert self.flapper.bids(1).tic == 0

        self.flapper.approve(directly())

        # when
        self.flapper.tend(1, Wad.from_number(20000), Wad.from_number(1.5)).transact()
        # then
        assert self.pie.balance_of(self.our_address) == Wad.from_number(49980000)
        assert self.gem.balance_of(pit) == Wad.from_number(0.5)
        # and
        assert self.flapper.bids(1).tic > 0

        # when
        self.flapper.tend(1, Wad.from_number(20000), Wad.from_number(2.0)).transact()
        # then
        assert self.pie.balance_of(self.our_address) == Wad.from_number(49980000)
        assert self.gem.balance_of(pit) == Wad.from_number(1.0)
        # and
        assert self.flapper.bids(1).tic > 0

        time_travel_by(self.web3, 60*60*24*8)

        # when
        self.flapper.deal(1).transact()
        # then
        assert self.pie.balance_of(self.our_address) == Wad.from_number(50000000)
        assert self.gem.balance_of(pit) == Wad.from_number(1.0)


class TestFlopper:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.pie = DSToken.deploy(self.web3, 'DAI')
        self.gem = DSToken.deploy(self.web3, 'MKR')
        self.flopper = Flopper.deploy(self.web3, self.pie.address, self.gem.address)

        # so the Flopper can mint MKR
        dad = DSGuard.deploy(self.web3)
        dad.permit(self.flopper.address, self.gem.address, DSGuard.ANY).transact()
        self.gem.set_authority(dad.address).transact()

    def test_era(self):
        assert self.flopper.era() > 1000000

    def test_pie(self):
        assert self.flopper.pie() == self.pie.address

    def test_gem(self):
        assert self.flopper.gem() == self.gem.address

    def test_beg(self):
        assert self.flopper.beg() == Wad.from_number(1.05)

    def test_ttl(self):
        assert self.flopper.ttl() == 3*60*60

    def test_tau(self):
        assert self.flopper.tau() == 7*24*60*60

    def test_read(self):
        # given
        recipient = Address(self.web3.eth.accounts[1])
        # and
        self.pie.mint(Wad.from_number(50000000)).transact()

        # expect
        assert self.flopper.kicks() == 0

        # when
        self.flopper.kick(recipient, Wad.from_number(10), Wad.from_number(20000)).transact()
        # then
        assert self.flopper.kicks() == 1
        # and
        auction = self.flopper.bids(1)
        assert auction.bid == Wad.from_number(20000)
        assert auction.lot == Wad.from_number(10)
        assert auction.guy == recipient
        assert auction.tic == 0
        assert auction.end > 0

    def test_scenario(self):
        # given
        recipient = Address(self.web3.eth.accounts[1])
        # and
        self.pie.mint(Wad.from_number(50000000)).transact()

        # when
        self.flopper.kick(recipient, Wad.from_number(10), Wad.from_number(20000)).transact()
        # then
        assert self.pie.balance_of(recipient) == Wad(0)
        assert self.gem.total_supply() == Wad(0)
        # and
        assert self.flopper.bids(1).tic == 0

        self.flopper.approve(directly())

        # when
        self.flopper.dent(1, Wad.from_number(9), Wad.from_number(20000)).transact()
        # then
        assert self.pie.balance_of(recipient) == Wad.from_number(20000)
        assert self.gem.total_supply() == Wad(0)
        # and
        assert self.flopper.bids(1).tic > 0

        # when
        self.flopper.dent(1, Wad.from_number(8), Wad.from_number(20000)).transact()
        # then
        assert self.pie.balance_of(recipient) == Wad.from_number(20000)
        assert self.gem.total_supply() == Wad(0)
        # and
        assert self.flopper.bids(1).tic > 0

        time_travel_by(self.web3, 60*60*24*8)

        # when
        self.flopper.deal(1).transact()
        # then
        assert self.pie.balance_of(recipient) == Wad.from_number(20000)
        assert self.gem.total_supply() == Wad.from_number(8)
