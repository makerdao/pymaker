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

import asyncio

import pytest
from web3 import EthereumTesterProvider
from web3 import Web3

from api import Address
from api import Wad
from api.approval import directly, via_tx_manager
from api.token import DSToken
from api.transact import TxManager, Invocation
from api.util import synchronize, int_to_bytes32, bytes_to_int, bytes_to_hexstring, hexstring_to_bytes


def setup_module():
    global web3, our_address, second_address, token

    web3 = Web3(EthereumTesterProvider())
    web3.eth.defaultAccount = web3.eth.accounts[0]
    our_address = Address(web3.eth.defaultAccount)
    second_address = Address(web3.eth.accounts[1])
    token = DSToken.deploy(web3, 'ABC')


def test_direct_approval():
    # given
    global web3, our_address, second_address, token

    # when
    directly()(token, second_address, "some-name")

    # then
    assert token.allowance_of(our_address, second_address) == Wad(2**256-1)


def test_direct_approval_should_not_approve_if_already_approved():
    # given
    global web3, our_address, second_address, token
    token.approve(second_address, Wad(2**248+17))

    # when
    directly()(token, second_address, "some-name")

    # then
    assert token.allowance_of(our_address, second_address) == Wad(2**248+17)


def test_via_tx_manager_approval():
    # given
    global web3, our_address, second_address, token
    tx = TxManager.deploy(web3)

    # when
    via_tx_manager(tx)(token, second_address, "some-name")

    # then
    assert token.allowance_of(tx.address, second_address) == Wad(2**256-1)


def test_via_tx_manager_should_not_approve_if_already_approved():
    # given
    global web3, our_address, second_address, token
    tx = TxManager.deploy(web3)
    tx.execute([], [Invocation(token.address, token.approve_calldata(second_address, Wad(2**248+19)))])

    # when
    via_tx_manager(tx)(token, second_address, "some-name")

    # then
    assert token.allowance_of(tx.address, second_address) == Wad(2**248+19)


