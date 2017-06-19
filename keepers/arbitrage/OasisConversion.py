#!/usr/bin/env python3
#
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

from api.Ray import Ray
from api.otc import SimpleMarket
from api.sai import Tub
from keepers.arbitrage.Conversion import Conversion


class OasisConversion(Conversion):
    def __init__(self, tub: Tub, market: SimpleMarket, offer_id: int):
        self.tub = tub
        self.market = market
        self.offer_id = offer_id

        offer = market.get_offer(offer_id)

        super().__init__(self._currency_symbol(offer.buy_which_token.address),
                         self._currency_symbol(offer.sell_which_token.address),
                         self.sell_to_buy_price(offer), #TODO don't know if this is the right price
                         offer.buy_how_much,
                         0.6,
                         'oasis-take-' + str(self.offer_id))

    def sell_to_buy_price(self, offer):
        return Ray(offer.sell_how_much)/Ray(offer.buy_how_much)

    def buy_to_sell_price(self, offer):
        return Ray(offer.sell_how_much)/Ray(offer.buy_how_much)

    def _currency_symbol(self, address):
        if address == self.tub.sai():
            return "SAI"
        elif address == self.tub.skr():
            return "SKR"
        elif address == self.tub.gem():
            return "ETH"
        else:
            return "___"

    def perform(self, from_amount):
        raise Exception("BUST Not implemented")
