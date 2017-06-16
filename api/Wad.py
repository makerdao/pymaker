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

from functools import total_ordering
from decimal import Decimal, ROUND_DOWN


@total_ordering
class Wad:
    """Represents a number with 18 decimal places. `Wad`, along with `Ray`, are the two basic numeric types
    used by Maker contracts.

    `Wad` implements comparison, addition, subtraction, multiplication and division operators. Comparison, addition,
    subtraction and division only work with other instances of `Wad`. Multiplication works with instances
    of `Wad` and `Ray` and also with `int` numbers. The result of multiplication is always a `Wad`.

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
        from api.Ray import Ray
        if isinstance(value, Wad):
            self.value = value.value
        elif isinstance(value, Ray):
            self.value = int((Decimal(value.value) / (Decimal(10)**Decimal(9))).quantize(1, rounding=ROUND_DOWN))
        elif isinstance(value, int):
            assert(value >= 0)
            self.value = value
        else:
            raise ArithmeticError

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
            result = Decimal(self.value) * Decimal(other.value) / (Decimal(10) ** Decimal(18))
            return Wad(int(result.quantize(1, rounding=ROUND_DOWN)))
        elif isinstance(other, Ray):
            result = Decimal(self.value) * Decimal(other.value) / (Decimal(10) ** Decimal(27))
            return Wad(int(result.quantize(1, rounding=ROUND_DOWN)))
        elif isinstance(other, int):
            return Wad((Decimal(self.value) * Decimal(other)).quantize(1))
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

    def __lt__(self, other):
        if isinstance(other, Wad):
            return self.value < other.value
        else:
            raise ArithmeticError

    def __cmp__(self, other):
        if isinstance(other, Wad):
            if self.value < other.value:
                return -1
            elif self.value > other.value:
                return 1
            else:
                return 0
        else:
            raise ArithmeticError

    #TODO remove this method from the API
    def percentage_change(self, change):
        return Wad((self.value * (100 + change)) // 100)

    @staticmethod
    # TODO try to implement a variable argument min()
    def min(first, second):
        """Returns the lower of the two Wad values"""
        if not isinstance(first, Wad) or not isinstance(second, Wad):
            raise ArithmeticError
        return Wad(min(first.value, second.value))

    @staticmethod
    # TODO try to implement a variable argument max()
    def max(first, second):
        """Returns the higher of the two Wad values"""
        if not isinstance(first, Wad) or not isinstance(second, Wad):
            raise ArithmeticError
        return Wad(max(first.value, second.value))
