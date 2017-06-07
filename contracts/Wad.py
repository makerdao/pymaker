import math
from functools import total_ordering


# TODO the math here is untested and probably in many cases the rounding
# is done wrong. use on your own responsibility

@total_ordering
class Wad:
    def __init__(self, value):
        assert(value >= 0)
        self.value = int(value)

    def __repr__(self):
        return "Wad(" + str(self.value) + ")"

    def __str__(self):
        tmp = str(self.value).zfill(19)
        return tmp[0:len(tmp)-18] + "." + tmp[len(tmp)-18:len(tmp)]

    def __add__(self, other):
        return Wad(self.value + other.value)

    def __sub__(self, other):
        return Wad(self.value - other.value)

    def __mul__(self, other):
        from contracts.Ray import Ray
        if isinstance(other, Wad):
            return Wad(int(math.ceil(self.value * other.value)) // int(math.pow(10, 18)))
        elif isinstance(other, Ray):
            return Ray(int(math.ceil(self.value * other.value)) // int(math.pow(10, 18)))
        else:
            return Wad(int(math.ceil(self.value * other)))

    def __truediv__(self, other):
        if isinstance(other, Wad):
            return self.value/other.value
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
