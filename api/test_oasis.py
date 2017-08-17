# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
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

from web3 import EthereumTesterProvider
from web3 import Web3

from api import Address, Wad
from api.approval import directly
from api.oasis import SimpleMarket, LogMake
from api.token import DSToken


class TestSimpleMarket:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.otc = SimpleMarket.deploy(self.web3)
        self.token1 = DSToken.deploy(self.web3, 'AAA')
        self.token1.mint(Wad.from_number(100)).transact()
        self.token2 = DSToken.deploy(self.web3, 'BBB')
        self.token2.mint(Wad.from_number(100)).transact()

    def test_approve_and_make_and_getters(self):
        # given
        assert self.otc.get_last_offer_id() == 0

        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # then
        assert self.otc.get_last_offer_id() == 1

        # and
        assert self.otc.get_offer(1).offer_id == 1
        assert self.otc.get_offer(1).sell_which_token == self.token1.address
        assert self.otc.get_offer(1).sell_how_much == Wad.from_number(1)
        assert self.otc.get_offer(1).buy_which_token == self.token2.address
        assert self.otc.get_offer(1).buy_how_much == Wad.from_number(2)
        assert self.otc.get_offer(1).owner == self.our_address
        assert self.otc.get_offer(1).timestamp != 0

        # and
        assert self.otc.active_offers() == [self.otc.get_offer(1)]

    def test_offer_comparison(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # and
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(3),
                      want_token=self.token2.address, want_amount=Wad.from_number(4)).transact()

        # then
        assert self.otc.get_last_offer_id() == 2
        assert self.otc.get_offer(1) == self.otc.get_offer(1)
        assert self.otc.get_offer(1) != self.otc.get_offer(2)

    def test_take_partial(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # when
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.25))

        # then
        assert self.otc.get_offer(1).sell_how_much == Wad.from_number(0.75)
        assert self.otc.get_offer(1).buy_how_much == Wad.from_number(1.5)
        assert self.otc.active_offers() == [self.otc.get_offer(1)]
        assert self.otc.get_last_offer_id() == 1

    def test_take_complete(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # when
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(1))

        # then
        assert self.otc.get_offer(1) is None
        assert self.otc.active_offers() == []
        assert self.otc.get_last_offer_id() == 1

    def test_kill(self):
        # given
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # when
        self.otc.kill(1).transact()

        # then
        assert self.otc.get_offer(1) is None
        assert self.otc.active_offers() == []
        assert self.otc.get_last_offer_id() == 1

    def test_past_make(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # then
        past_make = self.otc.past_make(100)
        assert len(past_make) == 1
        assert past_make[0].id == 1
        assert past_make[0].maker == self.our_address
        assert past_make[0].have_token == self.token1.address
        assert past_make[0].have_amount == Wad.from_number(1)
        assert past_make[0].want_token == self.token2.address
        assert past_make[0].want_amount == Wad.from_number(2)
        assert past_make[0].timestamp != 0

    def test_past_take(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # and
        self.otc.approve([self.token2], directly())
        self.otc.take(1, Wad.from_number(0.5))

        # then
        past_take = self.otc.past_take(100)
        assert len(past_take) == 1
        assert past_take[0].id == 1
        assert past_take[0].maker == self.our_address
        assert past_take[0].taker == self.our_address
        assert past_take[0].have_token == self.token1.address
        assert past_take[0].take_amount == Wad.from_number(0.5)
        assert past_take[0].want_token == self.token2.address
        assert past_take[0].give_amount == Wad.from_number(1)
        assert past_take[0].timestamp != 0

    def test_past_kill(self):
        # when
        self.otc.approve([self.token1], directly())
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # and
        self.otc.kill(1).transact()

        # then
        past_kill = self.otc.past_kill(100)
        assert len(past_kill) == 1
        assert past_kill[0].id == 1
        assert past_kill[0].maker == self.our_address
        assert past_kill[0].have_token == self.token1.address
        assert past_kill[0].have_amount == Wad.from_number(1)
        assert past_kill[0].want_token == self.token2.address
        assert past_kill[0].want_amount == Wad.from_number(2)
        assert past_kill[0].timestamp != 0

    def test_should_have_printable_representation(self):
        assert repr(self.otc) == f"SimpleMarket('{self.otc.address}')"
