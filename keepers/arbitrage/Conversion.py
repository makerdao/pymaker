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

from pprint import pformat

from api.Ray import Ray
from api.Wad import Wad


class Conversion:
    def __init__(self, from_currency: str, to_currency: str, rate: Ray, min_amount: Wad, max_amount: Wad, method: str):
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.rate = rate
        self.min_amount = min_amount #in `from_currency`
        self.max_amount = max_amount #in `from_currency`
        self.method = method

    def perform(self, from_amount):
        raise Exception("Not implemented")

    def __str__(self):
        return pformat(vars(self))

    def __repr__(self):
        return f"[{self.from_currency}->{self.to_currency} @{self.rate} by {self.method}]"
