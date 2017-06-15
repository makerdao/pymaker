# This file is part of "maker.py".
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

import datetime
from pprint import pformat

from contracts.Address import Address
from contracts.Contract import Contract
from contracts.Wad import Wad
from contracts.token.ERC20Token import ERC20Token


class SimpleMarket(Contract):
    abi = Contract._load_abi(__name__, 'SimpleMarket.abi')

    def __init__(self, web3, address):
        self._assert_contract_exists(web3, address)
        self.address = address
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)
        self._web3 = web3

    def get_last_offer_id(self):
        return self._contract.call().last_offer_id()

    def get_offer(self, offer_id):
        array = self._contract.call().offers(offer_id)
        if array[5] is not True:
            return None
        else:
            return OfferInfo(offer_id=offer_id,
                             sell_how_much=Wad(array[0]),
                             sell_which_token=ERC20Token(web3=self._web3, address=Address(array[1])),
                             buy_how_much=Wad(array[2]),
                             buy_which_token=ERC20Token(web3=self._web3, address=Address(array[3])),
                             owner=Address(array[4]),
                             active=array[5],
                             timestamp=datetime.datetime.fromtimestamp(array[6]))

    def make(self, have_token, want_token, have_amount, want_amount):
        try:
            tx_hash = self._contract.transact().make(have_token, want_token, have_amount, want_amount)
            return self._prepare_receipt(self._wait_for_receipt(tx_hash))
        except:
            return False

    def take(self, offer_id, quantity):
        try:
            tx_hash = self._contract.transact().take(self._to_bytes32(offer_id), quantity.value)
            return self._prepare_receipt(self._wait_for_receipt(tx_hash))
        except:
            return False

    def kill(self, offer_id):
        try:
            tx_hash = self._contract.transact().kill(self._to_bytes32(offer_id))
            return self._prepare_receipt(self._wait_for_receipt(tx_hash))
        except:
            return False


class OfferInfo:
    def __init__(self, offer_id, sell_how_much, sell_which_token, buy_how_much, buy_which_token, owner, active, timestamp):
        self.offer_id = offer_id
        self.sell_how_much = sell_how_much
        self.sell_which_token = sell_which_token
        self.buy_how_much = buy_how_much
        self.buy_which_token = buy_which_token
        self.owner = owner
        self.active = active
        self.timestamp = timestamp

    def __str__(self):
        return pformat(vars(self))
