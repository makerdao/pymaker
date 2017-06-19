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


class Conversion:
    def __init__(self, from_currency, to_currency, rate, fee_in_usd=None, method=None):
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.rate = rate
        self.rate_for_graph = float(-math.log(float(rate)))
        self.fee_in_usd = fee_in_usd
        self.method = method

    def __str__(self):
        return pformat(vars(self))

    def __repr__(self):
        return f"[{self.from_currency}->{self.to_currency} @{self.rate} by {self.method}]"
        # return pformat(vars(self))
