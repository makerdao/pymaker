import math
from functools import total_ordering

import re


@total_ordering
class Wad:
    def __init__(self, value):
        assert(value >= 0)
        self.value = int(value)

    def __repr__(self):
        return "Wad(" + str(self.value) + ")"

    def __str__(self):
        length = 24
        tmp = str(self.value).zfill(length)
        return re.sub("^(0+)", lambda m: ' '*len(m.group()), tmp[0:length-18]) + "." + tmp[length-18:length]

    def __add__(self, other):
        return Wad(self.value + other.value)

    def __sub__(self, other):
        return Wad(self.value - other.value)

    def __mul__(self, other):
        if isinstance(other, Wad):
            raise ArithmeticError
        return Wad(self.value * other)

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
