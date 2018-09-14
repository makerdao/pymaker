# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
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
from unittest.mock import MagicMock

import pytest
from web3 import HTTPProvider
from web3 import Web3

from pymaker import Address
from pymaker import Wad
from pymaker.approval import directly, via_tx_manager
from pymaker.gas import FixedGasPrice
from pymaker.token import DSToken
from pymaker.transactional import TxManager


class FailingTransact:
    def transact(self):
        return None

    async def transact_async(self):
        return None


def setup_module():
    global web3, our_address, second_address, third_address
    web3 = Web3(HTTPProvider("http://localhost:8555"))
    web3.eth.defaultAccount = web3.eth.accounts[0]
    our_address = Address(web3.eth.defaultAccount)
    second_address = Address(web3.eth.accounts[1])
    third_address = Address(web3.eth.accounts[2])


def setup_function():
    global token
    token = DSToken.deploy(web3, 'ABC')


def test_direct_approval():
    # given
    global web3, our_address, second_address, token

    # when
    directly()(token, second_address, "some-name")

    # then
    assert token.allowance_of(our_address, second_address) == Wad(2**256-1)


def test_direct_approval_should_obey_from_address():
    # given
    global web3, our_address, second_address, third_address, token
    # and
    # [there is already approval from the `defaultAccount`]
    # [so that we make sure we check for the existing approval properly]
    directly()(token, second_address, "some-name")

    # when
    directly(from_address=third_address)(token, second_address, "some-name")

    # then
    assert token.allowance_of(third_address, second_address) == Wad(2**256-1)


def test_direct_approval_should_obey_gas_price():
    # given
    global web3, our_address, second_address, token

    # when
    directly(gas_price=FixedGasPrice(25000000000))(token, second_address, "some-name")

    # then
    assert web3.eth.getBlock('latest', full_transactions=True).transactions[0].gasPrice == 25000000000


def test_direct_approval_should_not_approve_if_already_approved():
    # given
    global web3, our_address, second_address, token
    token.approve(second_address, Wad(2**248+17)).transact()

    # when
    directly()(token, second_address, "some-name")

    # then
    assert token.allowance_of(our_address, second_address) == Wad(2**248+17)


def test_direct_approval_should_raise_exception_if_approval_fails():
    # given
    global web3, our_address, second_address, token
    token.approve = MagicMock(return_value=FailingTransact())

    # expect
    with pytest.raises(Exception):
        directly()(token, second_address, "some-name")


def test_via_tx_manager_approval():
    # given
    global web3, our_address, second_address, token
    tx = TxManager.deploy(web3)

    # when
    via_tx_manager(tx)(token, second_address, "some-name")

    # then
    assert token.allowance_of(tx.address, second_address) == Wad(2**256-1)


def test_via_tx_manager_approval_should_obey_gas_price():
    # given
    global web3, our_address, second_address, token
    tx = TxManager.deploy(web3)

    # when
    via_tx_manager(tx, gas_price=FixedGasPrice(15000000000))(token, second_address, "some-name")

    # then
    assert web3.eth.getBlock('latest', full_transactions=True).transactions[0].gasPrice == 15000000000


def test_via_tx_manager_approval_should_not_approve_if_already_approved():
    # given
    global web3, our_address, second_address, token
    tx = TxManager.deploy(web3)
    tx.execute([], [token.approve(second_address, Wad(2**248+19)).invocation()]).transact()

    # when
    via_tx_manager(tx)(token, second_address, "some-name")

    # then
    assert token.allowance_of(tx.address, second_address) == Wad(2**248+19)


def test_via_tx_manager_approval_should_raise_exception_if_approval_fails():
    # given
    global web3, our_address, second_address, token
    tx = TxManager.deploy(web3)
    tx.execute = MagicMock(return_value=FailingTransact())

    # when
    with pytest.raises(Exception):
        via_tx_manager(tx)(token, second_address, "some-name")
