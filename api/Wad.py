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
from functools import total_ordering
from decimal import Decimal, ROUND_UP, ROUND_DOWN


# TODO the math here is untested and probably in many cases the rounding
# TODO is done wrong. for now use on your own responsibility
#
# TODO but the goal is to keep these classes to make Ray/Wad math easier

@total_ordering
class Wad:
    def __init__(self, value):
        from api.Ray import Ray
        if isinstance(value, Wad):
            self.value = value.value
        elif isinstance(value, Ray):
            self.value = int(value.value // int(math.pow(10, 9)))
        else:
            assert(value >= 0)
            self.value = int(value)

    @classmethod
    def from_number(cls, number):
        assert(number >= 0)
        pwr = Decimal(10) ** 18
        dec = Decimal(str(number)) * pwr
        return Wad(int(dec.quantize(1)))

    @classmethod
    def from_uint(cls, uint):
        return Wad(uint)

    def __repr__(self):
        return "Wad(" + str(self.value) + ")"

    def __str__(self):
        tmp = str(self.value).zfill(19)
        return tmp[0:len(tmp)-18] + "." + tmp[len(tmp)-18:len(tmp)]

    def __add__(self, other):
        if isinstance(other, Wad):
            return Wad(self.value + other.value)
        else:
            raise ArithmeticError

    def __sub__(self, other):
        if isinstance(other, Wad):
            return Wad(self.value - other.value)
        else:
            raise ArithmeticError

    # z = cast((uint256(x) * y + WAD / 2) / WAD);
    def __mul__(self, other):
        from api.Ray import Ray
        if isinstance(other, Wad):
            return Wad(int((Decimal(self.value) * Decimal(other.value) / Decimal(1000000000000000000)).quantize(1, rounding=ROUND_DOWN)))
        elif isinstance(other, Ray):
            return Wad(int((Decimal(self.value) * Decimal(other.value) / Decimal(1000000000000000000000000000)).quantize(1, rounding=ROUND_DOWN)))

            # TODO Wad should be returned, which means it should get divided by math.pow(10, 27)
            # return Ray(int(math.ceil(self.value * other.value)) // int(math.pow(10, 18)))
        elif isinstance(other, int):
            # raise ArithmeticError # DO WE NEED THIS??
            return Wad((Decimal(self.value) * Decimal(other)).quantize(1))
        else:
            raise ArithmeticError # DO WE NEED THIS??

    def __truediv__(self, other):
        from api.Ray import Ray
        if isinstance(other, Wad):
            return self.value/other.value
        elif isinstance(other, Ray):
            return self.value/other.value * int(math.pow(10, 9))
        else:
            return Wad(int(math.ceil(self.value/other)))

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __cmp__(self, other):
        if self.value < other.value:
            return -1
        elif self.value > other.value:
            return 1
        else:
            return 0

    #TODO remove this method from the API
    def percentage_change(self, change):
        return Wad((self.value * (100 + change)) // 100)

    @staticmethod
    def min(first, second):
        if not isinstance(first, Wad) or not isinstance(second, Wad):
            raise ArithmeticError
        return Wad(min(first.value, second.value))

    @staticmethod
    def max(first, second):
        if not isinstance(first, Wad) or not isinstance(second, Wad):
            raise ArithmeticError
        return Wad(max(first.value, second.value))
