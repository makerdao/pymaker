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

import pytest

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.token.ERC20Token import ERC20Token
from keepers.arbitrage.conversion import Conversion


@pytest.fixture(autouse=True)
def register_tokens(token1, token2):
    ERC20Token.register_token(token1, 'TK1')
    ERC20Token.register_token(token2, 'TK2')


@pytest.fixture
def token1():
    return Address('0x0101010101010101010101010101010101010101')


@pytest.fixture
def token2():
    return Address('0x0202020202020202020202020202020202020202')


def test_nicely_convert_to_string_without_amounts(token1, token2):
    # given
    conversion = Conversion(token1, token2, Ray.from_number(1.01), Wad.from_number(1000), 'met()')

    # expect
    assert str(conversion) == "[TK1 -> TK2 @1.010000000000000000000000000 by met() (max=1000.000000000000000000 TK1)]"


def test_nicely_convert_to_string_with_amounts(token1, token2):
    # given
    conversion = Conversion(token1, token2, Ray.from_number(1.01), Wad.from_number(1000), 'met()')
    conversion.source_amount = Wad.from_number(50)
    conversion.target_amount = Wad.from_number(50.5)

    # expect
    assert str(conversion) == "[50.000000000000000000 TK1 -> 50.500000000000000000 TK2 @1.010000000000000000000000000" \
                              " by met() (max=1000.000000000000000000 TK1)]"
