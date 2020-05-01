# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2020 EdNoepel
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

from pymaker import Address, Wad
from pymaker.model import Token


class TestToken:
    def setup_class(self):
        self.token = Token("COW", Address('0xbeef00000000000000000000000000000000BEEF'), 4)

    def test_convert(self):
        # two
        chain_amount = Wad(20000)
        assert self.token.normalize_amount(chain_amount) == Wad.from_number(2)

        # three
        normalized_amount = Wad.from_number(3)
        assert self.token.unnormalize_amount(normalized_amount) == Wad(30000)

    def test_min_amount(self):
        assert self.token.min_amount == Wad.from_number(0.0001)
        assert float(self.token.min_amount) == 0.0001
        assert self.token.unnormalize_amount(self.token.min_amount) == Wad(1)

        assert Wad.from_number(0.0004) > self.token.min_amount
        assert Wad.from_number(0.00005) < self.token.min_amount

        assert self.token.unnormalize_amount(Wad.from_number(0.0006)) > self.token.unnormalize_amount(self.token.min_amount)
        assert self.token.unnormalize_amount(Wad.from_number(0.00007)) < self.token.unnormalize_amount(self.token.min_amount)
        assert self.token.unnormalize_amount(Wad.from_number(0.00008)) == Wad(0)
