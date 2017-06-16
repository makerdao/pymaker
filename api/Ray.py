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
from decimal import *


# TODO the math here is untested and probably in many cases the rounding
# TODO is done wrong. for now use on your own responsibility
#
# TODO but the goal is to keep these classes to make Ray/Wad math easier

@total_ordering
class Ray:
    def __init__(self, value):
        assert(value >= 0)
        self.value = int(value)

    @classmethod
    def from_number(cls, number):
        assert(number >= 0)
        pwr = Decimal(10) ** 27
        dec = Decimal(str(number)) * pwr
        return Ray(int(dec.quantize(1)))

    def __repr__(self):
        return "Ray(" + str(self.value) + ")"

    def __str__(self):
        tmp = str(self.value).zfill(28)
        return tmp[0:len(tmp)-27] + "." + tmp[len(tmp)-27:len(tmp)]

    def __add__(self, other):
        return Ray(self.value + other.value)

    def __sub__(self, other):
        return Ray(self.value - other.value)

    def __mul__(self, other):
        from api.Wad import Wad
        if isinstance(other, Ray):
            return Ray(int(math.ceil(self.value * other.value)) // int(math.pow(10, 27)))
        elif isinstance(other, Wad):
            return Ray(int(math.ceil(self.value * other.value)) // int(math.pow(10, 18)))
        else:
            return Ray(int(math.ceil(self.value * other)))

    def __truediv__(self, other):
        from api.Wad import Wad
        if isinstance(other, Ray):
            return self.value/other.value
        elif isinstance(other, Wad):
            return (self.value/other.value) / int(math.pow(10, 9))
        else:
            return Ray(int(math.ceil(self.value/other)))

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

    @staticmethod
    def min(first, second):
        if not isinstance(first, Ray) or not isinstance(second, Ray):
            raise ArithmeticError
        return Ray(min(first.value, second.value))

    @staticmethod
    def max(first, second):
        if not isinstance(first, Ray) or not isinstance(second, Ray):
            raise ArithmeticError
        return Ray(max(first.value, second.value))
