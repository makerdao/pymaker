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

from web3 import EthereumTesterProvider
from web3 import Web3

from pymaker import Address
from pymaker import Wad
from pymaker.approval import directly
from pymaker.token import DSToken
from pymaker.transactional import TxManager


class TestTxManager:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.other_address = Address(self.web3.eth.accounts[1])
        self.tx = TxManager.deploy(self.web3)
        self.token1 = DSToken.deploy(self.web3, 'ABC')
        self.token1.mint(Wad.from_number(1000000)).transact()
        self.token2 = DSToken.deploy(self.web3, 'DEF')

    def test_owner(self):
        assert self.tx.owner() == self.our_address

    def test_approve(self):
        # given
        assert self.token1.allowance_of(self.our_address, self.tx.address) == Wad(0)
        assert self.token2.allowance_of(self.our_address, self.tx.address) == Wad(0)

        # when
        self.tx.approve([self.token1, self.token2], directly())

        # then
        assert self.token1.allowance_of(self.our_address, self.tx.address) == Wad(2**256-1)
        assert self.token2.allowance_of(self.our_address, self.tx.address) == Wad(2**256-1)

    def test_execute_zero_calls(self):
        # given
        self.tx.approve([self.token1], directly())

        # when
        res = self.tx.execute([self.token1.address], []).transact()

        # then
        assert res.successful

    def test_execute_one_call(self):
        # given
        self.tx.approve([self.token1], directly())

        # when
        res = self.tx.execute([self.token1.address],
                              [self.token1.transfer(self.other_address, Wad.from_number(500)).invocation()]).transact()

        # then
        assert res.successful
        assert self.token1.balance_of(self.our_address) == Wad.from_number(999500)
        assert self.token1.balance_of(self.other_address) == Wad.from_number(500)

    def test_execute_one_call_fails_if_no_approval(self):
        # given
        # [no approval]

        # when
        res = self.tx.execute([self.token1.address],
                              [self.token1.transfer(self.other_address, Wad.from_number(500)).invocation()]).transact()

        # then
        assert res is None
        assert self.token1.balance_of(self.our_address) == Wad.from_number(1000000)
        assert self.token1.balance_of(self.other_address) == Wad.from_number(0)

    def test_should_have_printable_representation(self):
        assert repr(self.tx) == f"TxManager('{self.tx.address}')"
