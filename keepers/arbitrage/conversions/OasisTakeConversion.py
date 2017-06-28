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
    def __init__(self, otc: SimpleMarket, offer: OfferInfo):
        self.otc = otc
        self.offer = offer

        super().__init__(source_token=offer.buy_which_token,
                         target_token=offer.sell_which_token,
                         rate=Ray(offer.sell_how_much)/Ray(offer.buy_how_much),
                         min_from_amount=Wad.from_number(0),  #TODO will probably change after dust order limitation gets introduced
                         max_from_amount=offer.buy_how_much,
                         method=f"oasis-take-{self.offer.offer_id}")

    def name(self):
        return f"otc.take({self.offer.offer_id}, '{self.quantity()}')"

    def execute(self):
        take_result = self.otc.take(self.offer.offer_id, self.quantity())
        if take_result:
            our_address = Address(self.otc.web3.eth.defaultAccount)
            incoming_transfer_on_take = next(filter(lambda transfer: transfer.token_address == self.offer.sell_which_token and transfer.to_address == our_address, take_result.transfers))
            outgoing_transfer_on_take = next(filter(lambda transfer: transfer.token_address == self.offer.buy_which_token and transfer.from_address == our_address, take_result.transfers))
            print(
                f"  Take was successful, exchanged {outgoing_transfer_on_take.value} {self.source_token} to {incoming_transfer_on_take.value} {self.target_token}")
            return take_result
        else:
            print(f"  Take failed!")
            return None

    def quantity(self):
        quantity = self.to_amount

        # if by any chance rounding makes us want to buy more quantity than is available,
        # we just buy the whole lot
        if quantity > self.offer.sell_how_much:
            quantity = self.offer.sell_how_much

        # if by any chance rounding makes us want to buy only slightly less than the available lot,
        # we buy everything as this is probably what we wanted in the first place
        if self.offer.sell_how_much - quantity < Wad.from_number(0.0000000001):
            quantity = self.offer.sell_how_much

        return quantity
