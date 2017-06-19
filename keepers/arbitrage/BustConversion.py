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

from api.Ray import Ray
from api.Wad import Wad
from api.sai import Tub
from keepers.arbitrage.Conversion import Conversion


class BustConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        price_eth_skr = tub.per()
        price_sai_eth = tub.tag()
        price_sai_skr = price_eth_skr * price_sai_eth
        how_much_sai_can_tub_buy = tub.woe() - tub.joy() - Wad.from_number(0.1) # to account for the joy surplus that is constantly increasing
        super().__init__('SAI', 'SKR', (Ray.from_number(1) / price_sai_skr), how_much_sai_can_tub_buy, 0.6, 'tub-bust')

    def perform(self, from_amount):
        raise Exception("BUST Not implemented")
