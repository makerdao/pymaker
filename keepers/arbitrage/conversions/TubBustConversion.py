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

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.sai import Tub
from keepers.arbitrage.Conversion import Conversion


class TubBustConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(from_currency='SAI',
                         to_currency='SKR',
                         rate=(Ray.from_number(1) / (tub.per() * tub.tag())),
                         min_from_amount=Wad.from_number(0),
                         max_from_amount=self.bustable_amount_in_sai(tub),
                         method="tub-bust")

    def bustable_amount_in_sai(self, tub: Tub):
        #TODO we always try to bust 10 SAI less than what the Tub reports
        #in order to discount the growth of `joy()` that might've have happened since the last drip
        #of course this is not the right solution and it won't even work properly if the last
        #drip happened enough time ago
        return Wad.max(tub.woe() - tub.joy() - Wad.from_number(10), Wad.from_number(0))

    #TODO at some point a concept of spread on bust() will be introduced in the Tub
    #then this concept has to be moved here so the keeper understand the actual price
    #he can get on bust(), and on boom() as well
    def perform(self):
        print(f"  Executing bust('{self.to_amount}') in order to exchange {self.from_amount} SAI to {self.to_amount} SKR")
        bust_result = self.tub.bust(self.to_amount)
        if bust_result:
            our_address = Address(self.tub.web3.eth.defaultAccount)
            skr_transfer_on_bust = next(filter(lambda transfer: transfer.token_address == self.tub.skr() and transfer.to_address == our_address, bust_result.transfers))
            sai_transfer_on_bust = next(filter(lambda transfer: transfer.token_address == self.tub.sai() and transfer.from_address == our_address, bust_result.transfers))
            print(f"  Bust was successful, exchanged {sai_transfer_on_bust.value} SAI to {skr_transfer_on_bust.value} SKR")
            return bust_result
        else:
            print(f"  Bust failed!")
            return None
