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

from arbitrage_keeper.transfer_formatter import TransferFormatter
from pymaker import Address, Transfer
from pymaker.numeric import Wad
from pymaker.token import ERC20Token


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


@pytest.fixture
def our_address():
    return Address('0x5432154321543215432154321543215432154321')


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


def test_should_format_net_balances(token1, our_address, some_address):
    # given
    transfer1 = Transfer(token1, our_address, some_address, Wad.from_number(15))
    transfer2 = Transfer(token1, some_address, our_address, Wad.from_number(17))

    # expect
    assert TransferFormatter().format_net([transfer1, transfer2], our_address) \
        == "2.000000000000000000 TK1"


def test_should_format_net_balances_if_multiple_transfers(token1, our_address, some_address):
    # given
    transfer1 = Transfer(token1, our_address, some_address, Wad.from_number(15))
    transfer2 = Transfer(token1, some_address, our_address, Wad.from_number(17))
    transfer3 = Transfer(token1, some_address, our_address, Wad.from_number(3.5))

    # expect
    assert TransferFormatter().format_net([transfer1, transfer2, transfer3], our_address) \
        == "5.500000000000000000 TK1"


def test_should_format_net_balances_excluding_alien_transfers(token1, our_address, some_address):
    # given
    transfer1 = Transfer(token1, some_address, our_address, Wad.from_number(4))
    transfer2 = Transfer(token1, our_address, some_address, Wad.from_number(1.5))
    transfer3 = Transfer(token1, some_address, some_address, Wad.from_number(100))

    # expect
    assert TransferFormatter().format_net([transfer1, transfer2, transfer3], our_address) \
        == "2.500000000000000000 TK1"


def test_should_format_net_balances_excluding_transfers_between_us(token1, our_address, some_address):
    # given
    transfer1 = Transfer(token1, some_address, our_address, Wad.from_number(4))
    transfer2 = Transfer(token1, our_address, some_address, Wad.from_number(1.5))
    transfer3 = Transfer(token1, our_address, our_address, Wad.from_number(50))

    # expect
    assert TransferFormatter().format_net([transfer1, transfer2, transfer3], our_address) \
        == "2.500000000000000000 TK1"


def test_should_format_net_balances_for_more_than_one_token(token1, token2, our_address, some_address):
    # given
    transfer1 = Transfer(token1, our_address, some_address, Wad.from_number(15))
    transfer2 = Transfer(token1, some_address, our_address, Wad.from_number(17))
    transfer3 = Transfer(token2, our_address, some_address, Wad.from_number(2.5))
    transfer4 = Transfer(token2, some_address, our_address, Wad.from_number(100))

    # expect
    assert TransferFormatter().format_net([transfer1, transfer2, transfer3, transfer4], our_address) \
        == "2.000000000000000000 TK1 and 97.500000000000000000 TK2"


def test_should_not_include_zeros_in_net_balances(token1, token2, our_address, some_address):
    # given
    transfer1 = Transfer(token1, our_address, some_address, Wad.from_number(15))
    transfer2 = Transfer(token1, some_address, our_address, Wad.from_number(17))
    transfer3 = Transfer(token2, our_address, some_address, Wad.from_number(22.5))
    transfer4 = Transfer(token2, some_address, our_address, Wad.from_number(22.5))

    # expect
    assert TransferFormatter().format_net([transfer1, transfer2, transfer3, transfer4], our_address) \
        == "2.000000000000000000 TK1"


def test_support_iterators(token1, some_address):
    # given
    transfer = Transfer(token1, some_address, some_address, Wad.from_number(11.5))

    # expect
    assert TransferFormatter().format(iter([transfer])) == "11.500000000000000000 TK1"


