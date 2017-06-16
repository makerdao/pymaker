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
from typing import Optional

from web3 import Web3

from api.Address import Address
from api.Contract import Contract
from api.Receipt import Receipt
from api.Wad import Wad
from api.otc.OfferInfo import OfferInfo
from api.token.ERC20Token import ERC20Token


class SimpleMarket(Contract):
    abi = Contract._load_abi(__name__, 'SimpleMarket.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def get_last_offer_id(self) -> int:
        return self._contract.call().last_offer_id()

    # TODO introduce empty offer caching, as if an offer is None
    # it won't ever become not-None again
    def get_offer(self, offer_id) -> Optional[OfferInfo]:
        array = self._contract.call().offers(offer_id)
        if array[5] is not True:
            return None
        else:
            return OfferInfo(offer_id=offer_id,
                             sell_how_much=Wad(array[0]),
                             sell_which_token=ERC20Token(web3=self.web3, address=Address(array[1])),
                             buy_how_much=Wad(array[2]),
                             buy_which_token=ERC20Token(web3=self.web3, address=Address(array[3])),
                             owner=Address(array[4]),
                             active=array[5],
                             timestamp=datetime.datetime.fromtimestamp(array[6]))

    def make(self, have_token: Address, want_token: Address, have_amount: Wad, want_amount: Wad) -> Optional[Receipt]:
        """

        :param have_token:
        :param want_token:
        :param have_amount:
        :param want_amount:
        :return:
        """
        try:
            tx_hash = self._contract.transact().make(have_token.address, want_token.address,
                                                     have_amount.value, want_amount.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def take(self, offer_id: int, quantity: Wad) -> Optional[Receipt]:
        try:
            tx_hash = self._contract.transact().take(self._to_bytes32(offer_id), quantity.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def kill(self, offer_id: int) -> Optional[Receipt]:
        try:
            tx_hash = self._contract.transact().kill(self._to_bytes32(offer_id))
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None
