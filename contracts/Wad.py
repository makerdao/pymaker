import math
from functools import total_ordering


@total_ordering
class Wad:
    def __init__(self, value):
        # TODO check if non-negative
        # TODO do not use 'int' for internal representation
        self.value = int(math.ceil(value))

    def __repr__(self):
        return "Wad(" + str(self.value) + ")"

    def __str__(self):
        return "{:25.18f}".format(self.value/math.pow(10, 18))

    def __add__(self, other):
        # TODO check for overflow
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

    @staticmethod
    def min(first, second):
        if not isinstance(first, Wad) or not isinstance(second, Wad):
            raise ArithmeticError
        # TODO do not use 'int' for internal representation
        return Wad(min(first.value, second.value))

    @staticmethod
    def max(first, second):
        if not isinstance(first, Wad) or not isinstance(second, Wad):
            raise ArithmeticError
        # TODO do not use 'int' for internal representation
        return Wad(max(first.value, second.value))
