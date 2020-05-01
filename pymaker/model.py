# This file is part of Maker Keeper Framework.
# 
# Copyright (C) 2017-2018 mitakash
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

        self.min_amount = Wad.from_number(10 ** -self.decimals)

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
