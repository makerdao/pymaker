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
from functools import total_ordering, reduce
from decimal import *


@total_ordering
class Wad:
    """Represents a number with 18 decimal places.

    `Wad` implements comparison, addition, subtraction, multiplication and division operators. Comparison, addition,
    subtraction and division only work with other instances of `Wad`. Multiplication works with instances
    of `Wad` and `Ray` and also with `int` numbers. The result of multiplication is always a `Wad`.

    `Wad`, along with `Ray`, are the two basic numeric types used by Maker contracts.

    Notes:
        The internal representation of `Wad` is an unbounded integer, the last 18 digits of it being treated
        as decimal places. It is similar to the representation used in Maker contracts (`uint128`).
    """

    def __init__(self, value):
        """Creates a new Wad number.

        Args:
            value: an instance of `Wad`, `Ray` or an integer. In case of an integer, the internal representation
                of Maker contracts is used which means that passing `1` will create an instance of `Wad`
                with a value of `0.000000000000000001'.
        """
        if isinstance(value, Wad):
            self.value = value.value
        elif isinstance(value, Ray):
            self.value = int((Decimal(value.value) / (Decimal(10)**Decimal(9))).quantize(1, rounding=ROUND_DOWN))
        elif isinstance(value, int):
            # assert(value >= 0)
            self.value = value
        else:
            raise ArithmeticError

    @classmethod
    def from_number(cls, number):
        # assert(number >= 0)
        pwr = Decimal(10) ** 18
        dec = Decimal(str(number)) * pwr
        return Wad(int(dec.quantize(1)))

    def __repr__(self):
        return "Wad(" + str(self.value) + ")"

    def __str__(self):
        tmp = str(self.value).zfill(19)
        return (tmp[0:len(tmp)-18] + "." + tmp[len(tmp)-18:len(tmp)]).replace("-.", "-0.")

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
        if isinstance(other, Wad):
            result = Decimal(self.value) * Decimal(other.value) / (Decimal(10) ** Decimal(18))
            return Wad(int(result.quantize(1, rounding=ROUND_DOWN)))
        elif isinstance(other, Ray):
            result = Decimal(self.value) * Decimal(other.value) / (Decimal(10) ** Decimal(27))
            return Wad(int(result.quantize(1, rounding=ROUND_DOWN)))
        elif isinstance(other, int):
            return Wad(int((Decimal(self.value) * Decimal(other)).quantize(1)))
        else:
            raise ArithmeticError

    def __truediv__(self, other):
        if isinstance(other, Wad):
            return Wad(int((Decimal(self.value) * (Decimal(10) ** Decimal(18)) / Decimal(other.value)).quantize(1, rounding=ROUND_DOWN)))
        else:
            raise ArithmeticError

    def __eq__(self, other):
        if isinstance(other, Wad):
            return self.value == other.value
        else:
            raise ArithmeticError

    def __hash__(self):
        return hash(self.value)

    def __lt__(self, other):
        if isinstance(other, Wad):
            return self.value < other.value
        else:
            raise ArithmeticError

    @staticmethod
    def min(*args):
        """Returns the lower of the Wad values"""
        return reduce(lambda x, y: x if x < y else y, args[1:], args[0])

    @staticmethod
    def max(*args):
        """Returns the higher of the Wad values"""
        return reduce(lambda x, y: x if x > y else y, args[1:], args[0])


@total_ordering
class Ray:
    """Represents a number with 27 decimal places.

    `Ray` implements comparison, addition, subtraction, multiplication and division operators. Comparison, addition,
    subtraction and division only work with other instances of `Ray`. Multiplication works with instances
    of `Ray` and `And` and also with `int` numbers. The result of multiplication is always a `Ray`.

    `Ray`, along with `Wad`, are the two basic numeric types used by Maker contracts.

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
        if isinstance(value, Ray):
            self.value = value.value
        elif isinstance(value, Wad):
            self.value = int((Decimal(value.value) * (Decimal(10)**Decimal(9))).quantize(1))
        elif isinstance(value, int):
            # assert(value >= 0)
            self.value = value
        else:
            raise ArithmeticError

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
        return (tmp[0:len(tmp)-27] + "." + tmp[len(tmp)-27:len(tmp)]).replace("-.", "-0.")

    def __add__(self, other):
        if isinstance(other, Ray):
            return Ray(self.value + other.value)
        else:
            raise ArithmeticError

    def __sub__(self, other):
        if isinstance(other, Ray):
            return Ray(self.value - other.value)
        else:
            raise ArithmeticError

    def __mul__(self, other):
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

    def __hash__(self):
        return hash(self.value)

    def __lt__(self, other):
        if isinstance(other, Ray):
            return self.value < other.value
        else:
            raise ArithmeticError

    @staticmethod
    def min(*args):
        """Returns the lower of the Ray values"""
        return reduce(lambda x, y: x if x < y else y, args[1:], args[0])

    @staticmethod
    def max(*args):
        """Returns the higher of the Ray values"""
        return reduce(lambda x, y: x if x > y else y, args[1:], args[0])
