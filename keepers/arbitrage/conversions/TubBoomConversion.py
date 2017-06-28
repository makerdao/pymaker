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

import math
from pprint import pformat

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.sai import Tub
from keepers.arbitrage.conversion import Conversion


class TubBoomConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(source_token=self.tub.skr(),
                         target_token=self.tub.sai(),
                         rate=Ray(tub.tap_bid()),
                         max_source_amount=self.boomable_amount_in_skr(tub),
                         method="tub.boom()")

    #TODO currently the keeper doesn't see `joy` changing unless `drip` gets called
    #this is the thing `sai-explorer` is trying to calculate on his own
    def boomable_amount_in_sai(self, tub: Tub):
        return Wad.max(tub.joy() - tub.woe(), Wad.from_number(0))

    def boomable_amount_in_skr(self, tub: Tub):
        # we deduct 0.000001 in order to avoid rounding errors
        return Wad.max(Wad(self.boomable_amount_in_sai(tub) / (tub.tap_bid())) - Wad.from_number(0.000001), Wad.from_number(0))

    def name(self):
        return f"tub.boom('{self.source_amount}')"

    def execute(self):
        return self.tub.boom(self.source_amount)
