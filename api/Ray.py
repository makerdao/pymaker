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


@total_ordering
class Ray:
    """Represents a number with 27 decimal places. `Ray`, along with `Wad`, are the two basic numeric types
    used by Maker contracts.

    `Ray` implements comparison, addition, subtraction, multiplication and division operators. Comparison, addition,
    subtraction and division only work with other instances of `Ray`. Multiplication works with instances
    of `Ray` and `And` and also with `int` numbers. The result of multiplication is always a `Ray`.

    Notes:
        The internal representation of `Ray` is an unbounded integer, the last 27 digits of it being treated
        as decimal places. It is similar to the representation used in Maker contracts (`uint128`).
    """

    def __init__(self, value):
        """Creates a new Ray number.

        Args:
            value: an instance of `Ray`, `Wad` or an integer. In case of an integer, the internal representation
                of Maker contracts is used which means that passing `1` will create an instance of `Ray`
                with a value of `0.000000000000000000000000001'.
        """
        from api.Wad import Wad
        if isinstance(value, Ray):
            self.value = value.value
        elif isinstance(value, Wad):
            self.value = int((Decimal(value.value) * (Decimal(10)**Decimal(9))).quantize(1))
        elif isinstance(value, int):
            assert(value >= 0)
            self.value = value
        else:
            raise ArithmeticError

    @classmethod
    def from_number(cls, number):
        assert(number >= 0)
        pwr = Decimal(10) ** 27
        dec = Decimal(str(number)) * pwr
        return Ray(int(dec.quantize(1)))

    @classmethod
    def from_uint(cls, uint):
        return Ray(uint)

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
            result = Decimal(self.value) * Decimal(other.value) / (Decimal(10) ** Decimal(27))
            return Ray(int(result.quantize(1, rounding=ROUND_DOWN)))
        elif isinstance(other, Wad):
            result = Decimal(self.value) * Decimal(other.value) / (Decimal(10) ** Decimal(18))
            return Ray(int(result.quantize(1, rounding=ROUND_DOWN)))
        elif isinstance(other, int):
            return Ray(int((Decimal(self.value) * Decimal(other)).quantize(1)))
        else:
            raise ArithmeticError

    def __truediv__(self, other):
        if isinstance(other, Ray):
            return Ray(int((Decimal(self.value) * (Decimal(10) ** Decimal(27)) / Decimal(other.value)).quantize(1, rounding=ROUND_DOWN)))
        else:
            raise ArithmeticError

    def __eq__(self, other):
        if isinstance(other, Ray):
            return self.value == other.value
        else:
            raise ArithmeticError

    def __lt__(self, other):
        if isinstance(other, Ray):
            return self.value < other.value
        else:
            raise ArithmeticError

    def __cmp__(self, other):
        if isinstance(other, Ray):
            if self.value < other.value:
                return -1
            elif self.value > other.value:
                return 1
            else:
                return 0
        else:
            raise ArithmeticError

    @staticmethod
    # TODO try to implement a variable argument min()
    def min(first, second):
        """Returns the lower of the two Ray values"""
        if not isinstance(first, Ray) or not isinstance(second, Ray):
            raise ArithmeticError
        return Ray(min(first.value, second.value))

    @staticmethod
    # TODO try to implement a variable argument max()
    def max(first, second):
        """Returns the higher of the two Ray values"""
        if not isinstance(first, Ray) or not isinstance(second, Ray):
            raise ArithmeticError
        return Ray(max(first.value, second.value))
