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

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.otc import SimpleMarket
from api.otc.OfferInfo import OfferInfo
from api.sai import Tub
from keepers.arbitrage.Conversion import Conversion


class OasisTakeConversion(Conversion):
    def __init__(self, tub: Tub, market: SimpleMarket, offer: OfferInfo):
        self.tub = tub
        self.market = market
        self.offer = offer

        super().__init__(from_currency=self._currency_symbol(offer.buy_which_token.address),
                         to_currency=self._currency_symbol(offer.sell_which_token.address),
                         rate=Ray(offer.sell_how_much)/Ray(offer.buy_how_much),
                         min_from_amount=Wad.from_number(0),  #TODO will probably change after dust order limitation gets introduced
                         max_from_amount=offer.buy_how_much,
                         method=f"oasis-take-{self.offer.offer_id}")

    def _currency_symbol(self, address):
        if address == self.tub.sai():
            return "SAI"
        elif address == self.tub.skr():
            return "SKR"
        elif address == self.tub.gem():
            return "ETH"
        else:
            return "___"

    def perform(self):
        quantity = self.to_amount

        # if by any chance rounding makes us want to buy more quantity than is available,
        # we just buy the whole lot
        if quantity > self.offer.sell_how_much:
            quantity = self.offer.sell_how_much

        # if by any chance rounding makes us want to buy only slightly less than the available lot,
        # we buy everything as this is probably what we wanted in the first place
        if self.offer.sell_how_much - quantity < Wad.from_number(0.0000000001):
            quantity = self.offer.sell_how_much

        print(f"  Executing take({self.offer.offer_id}, '{quantity}') on OasisDEX in order to exchange {self.from_amount} {self.from_currency} to {self.to_amount} {self.to_currency}")
        take_result = self.market.take(self.offer.offer_id, quantity)
        if take_result:
            our_address = Address(self.tub.web3.eth.defaultAccount)
            incoming_transfer_on_take = next(filter(lambda transfer: transfer.token_address == self.offer.sell_which_token.address and transfer.to_address == our_address, take_result.transfers))
            outgoing_transfer_on_take = next(filter(lambda transfer: transfer.token_address == self.offer.buy_which_token.address and transfer.from_address == our_address, take_result.transfers))
            print(f"  Take was successful, exchanged {outgoing_transfer_on_take.value} {self.from_currency} to {incoming_transfer_on_take.value} {self.to_currency}")
            return take_result
        else:
            print(f"  Take failed!")
            return None
