import math
from functools import total_ordering

# TODO the math here is untested and probably in many cases the rounding
# is done wrong. use on your own responsibility

@total_ordering
class Ray:
    def __init__(self, value):
        assert(value >= 0)
        self.value = int(value)

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
        from contracts.Wad import Wad
        if isinstance(other, Ray):
            return Ray(int(math.ceil(self.value * other.value)) // int(math.pow(10, 27)))
        elif isinstance(other, Wad):
            return Ray(int(math.ceil(self.value * other.value)) // int(math.pow(10, 18)))
        else:
            return Ray(int(math.ceil(self.value * other)))

    def __truediv__(self, other):
        from contracts.Wad import Wad
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
