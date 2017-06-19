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


class BoomConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(from_currency='SKR',
                         to_currency='SAI',
                         rate=(tub.per() * tub.tag()),
                         min_from_amount=Wad.from_number(0),
                         max_from_amount=self.boomable_amount_in_skr(tub),
                         method="tub-boom")

    def boomable_amount_in_skr(self, tub: Tub):
        return Wad(Ray(tub.joy()) / (tub.per() * tub.tag()))

    def perform(self):
        raise Exception("BOOM Not implemented")
