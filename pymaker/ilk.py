# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019-2021 EdNoepel
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

from typing import Optional
from web3 import Web3

from pymaker.numeric import Wad, Ray, Rad


class Ilk:
    """Models one collateral type, the combination of a token and a set of risk parameters.
    For example, ETH-A and ETH-B are different collateral types with the same underlying token (WETH) but with
    different risk parameters.
    """

    def __init__(self, name: str, rate: Optional[Ray] = None,
                 ink: Optional[Wad] = None,
                 art: Optional[Wad] = None,
                 spot: Optional[Ray] = None,
                 line: Optional[Rad] = None,
                 dust: Optional[Rad] = None):
        assert (isinstance(name, str))
        assert (isinstance(rate, Ray) or (rate is None))
        assert (isinstance(ink, Wad) or (ink is None))
        assert (isinstance(art, Wad) or (art is None))
        assert (isinstance(spot, Ray) or (spot is None))
        assert (isinstance(line, Rad) or (line is None))
        assert (isinstance(dust, Rad) or (dust is None))

        self.name = name
        self.rate = rate
        self.ink = ink
        self.art = art
        self.spot = spot
        self.line = line
        self.dust = dust

    def toBytes(self):
        return Web3.toBytes(text=self.name).ljust(32, bytes(1))

    @staticmethod
    def fromBytes(ilk: bytes):
        assert (isinstance(ilk, bytes))

        name = Web3.toText(ilk.strip(bytes(1)))
        return Ilk(name)

    def __eq__(self, other):
        assert isinstance(other, Ilk)

        return (self.name == other.name) \
           and (self.rate == other.rate) \
           and (self.ink == other.ink) \
           and (self.art == other.art) \
           and (self.spot == other.spot) \
           and (self.line == other.line) \
           and (self.dust == other.dust)

    def __repr__(self):
        repr = ''
        if self.rate:
            repr += f' rate={self.rate}'
        if self.ink:
            repr += f' Ink={self.ink}'
        if self.art:
            repr += f' Art={self.art}'
        if self.spot:
            repr += f' spot={self.spot}'
        if self.line:
            repr += f' line={self.line}'
        if self.dust:
            repr += f' dust={self.dust}'
        if repr:
            repr = f'[{repr.strip()}]'

        return f"Ilk('{self.name}'){repr}"
