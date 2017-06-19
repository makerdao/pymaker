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

import math
from pprint import pformat

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.sai import Tub
from keepers.arbitrage.Conversion import Conversion


class TubBoomConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(from_currency='SKR',
                         to_currency='SAI',
                         rate=(tub.per() * tub.tag()),
                         min_from_amount=Wad.from_number(0),
                         max_from_amount=self.boomable_amount_in_skr(tub),
                         method="tub-boom")

    #TODO currently the keeper doesn't see `joy` changing unless `drip` gets called
    #this is the thing `sai-explorer` is trying to calculate on his own
    def boomable_amount_in_sai(self, tub: Tub):
        return Wad.max(tub.joy() - tub.woe(), Wad.from_number(0))

    def boomable_amount_in_skr(self, tub: Tub):
        return Wad(Ray(self.boomable_amount_in_sai(tub)) / (tub.per() * tub.tag()))

    #TODO at some point a concept of spread on boom()/bust() will be introduced in the Tub
    #then this concept has to be moved here so the keeper understand the actual price
    #he can get on bust(), and on boom() as well
    def perform(self):
        print(f"  Executing boom('{self.from_amount}') in order to exchange {self.from_amount} SKR to {self.to_amount} SAI")
        boom_result = self.tub.boom(self.from_amount)
        if boom_result:
            our_address = Address(self.tub.web3.eth.defaultAccount)
            skr_transfer_on_boom = next(filter(lambda transfer: transfer.token_address == self.tub.skr() and transfer.from_address == our_address, boom_result.transfers))
            sai_transfer_on_boom = next(filter(lambda transfer: transfer.token_address == self.tub.sai() and transfer.to_address == our_address, boom_result.transfers))
            print(f"  Boom was successful, exchanged {skr_transfer_on_boom.value} SKR to {sai_transfer_on_boom.value} SAI")
            return boom_result
        else:
            print(f"  Boom failed!")
            return None
