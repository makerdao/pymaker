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
from api.Transfer import Transfer
from api.Wad import Wad
from api.token.ERC20Token import ERC20Token
from keepers.arbitrage.transfer_formatter import TransferFormatter


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


@pytest.fixture
def some_address():
    return Address('0x1234512345123451234512345123451234512345')


def test_should_return_empty_string_when_no_transfers():
    # expect
    assert TransferFormatter().format([]) == ""


def test_should_format_single_transfer(token1, some_address):
    # given
    transfer = Transfer(token1, some_address, some_address, Wad.from_number(105))

    # expect
    assert TransferFormatter().format([transfer]) == "105.000000000000000000 TK1"


def test_should_format_two_different_tokens(token1, token2, some_address):
    # given
    transfer1 = Transfer(token1, some_address, some_address, Wad.from_number(105))
    transfer2 = Transfer(token2, some_address, some_address, Wad.from_number(17))

    # expect
    assert TransferFormatter().format([transfer1, transfer2]) \
        == "105.000000000000000000 TK1 and 17.000000000000000000 TK2"


def test_support_iterators(token1, some_address):
    # given
    transfer = Transfer(token1, some_address, some_address, Wad.from_number(11.5))

    # expect
    assert TransferFormatter().format(iter([transfer])) == "11.500000000000000000 TK1"


