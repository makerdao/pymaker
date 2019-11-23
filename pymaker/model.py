from pprint import pformat
from typing import Optional, List

from pymaker import Address
from pymaker.numeric import Wad


class Token:
    def __init__(self, name: str, address: Optional[Address], decimals: int):
        assert(isinstance(name, str))
        assert(isinstance(address, Address) or (address is None))
        assert(isinstance(decimals, int))

        self.name = name
        self.address = address
        self.decimals = decimals

    def normalize_amount(self, amount: Wad) -> Wad:
        assert(isinstance(amount, Wad))

        return amount * Wad.from_number(10 ** (18 - self.decimals))

    def unnormalize_amount(self, amount: Wad) -> Wad:
        assert(isinstance(amount, Wad))

        return amount * Wad.from_number(10 ** (self.decimals - 18))

    def is_eth(self) -> bool:
        return self.address == Address('0x0000000000000000000000000000000000000000')

    def __eq__(self, other):
        assert(isinstance(other, Token))
        return self.name == other.name and \
               self.address == other.address and \
               self.decimals == other.decimals

    def __hash__(self):
        return hash((self.name, self.address, self.decimals))

    def __str__(self):
        return self.name

    def __repr__(self):
        return pformat(vars(self))


