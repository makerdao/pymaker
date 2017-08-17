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
from api.oasis import SimpleMarket
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

    def test_approve_and_make_and_get_last_offer_id_and_get_offer(self):
        # given
        self.otc.approve([self.token1], directly())

        # and
        assert self.otc.get_last_offer_id() == 0

        # when
        self.otc.make(have_token=self.token1.address, have_amount=Wad.from_number(1),
                      want_token=self.token2.address, want_amount=Wad.from_number(2)).transact()

        # then
        assert self.otc.get_last_offer_id() == 1
        assert self.otc.get_offer(1).offer_id == 1
        assert self.otc.get_offer(1).sell_which_token == self.token1.address
        assert self.otc.get_offer(1).sell_how_much == Wad.from_number(1)
        assert self.otc.get_offer(1).buy_which_token == self.token2.address
        assert self.otc.get_offer(1).buy_how_much == Wad.from_number(2)
        assert self.otc.get_offer(1).owner == self.our_address

    def test_should_have_printable_representation(self):
        assert repr(self.otc) == f"SimpleMarket('{self.otc.address}')"
