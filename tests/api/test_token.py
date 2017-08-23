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
from keeper.api import Address
from keeper.api.numeric import Wad
from keeper.api.util import synchronize
from web3 import EthereumTesterProvider
from web3 import Web3

from keeper.api.token import DSToken, DSEthToken, ERC20Token


class TestERC20Token:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.second_address = Address(self.web3.eth.accounts[1])
        self.token = DSToken.deploy(self.web3, 'ABC')
        self.token.mint(Wad(1000000)).transact()

    def test_token_registry(self):
        # given
        ERC20Token.register_token(Address('0x0100000000000000000000000000000000000000'), 'ABC')
        ERC20Token.register_token(Address('0x0200000000000000000000000000000000000000'), 'DEF')
        ERC20Token.register_token(Address('0x0300000000000000000000000000000000000000'), 'GHI')

        # expect
        assert ERC20Token.token_name_by_address(Address('0x0100000000000000000000000000000000000000')) == 'ABC'
        assert ERC20Token.token_name_by_address(Address('0x0200000000000000000000000000000000000000')) == 'DEF'
        assert ERC20Token.token_name_by_address(Address('0x0300000000000000000000000000000000000000')) == 'GHI'
        with pytest.raises(Exception):
            assert ERC20Token.token_name_by_address(Address('0x0400000000000000000000000000000000000000'))

        # and
        assert ERC20Token.token_address_by_name('ABC') == Address('0x0100000000000000000000000000000000000000')
        assert ERC20Token.token_address_by_name('DEF') == Address('0x0200000000000000000000000000000000000000')
        assert ERC20Token.token_address_by_name('GHI') == Address('0x0300000000000000000000000000000000000000')
        with pytest.raises(Exception):
            ERC20Token.token_address_by_name('XXX')

    def test_total_supply(self):
        assert self.token.total_supply() == Wad(1000000)

    def test_balance_of(self):
        assert self.token.balance_of(self.our_address) == Wad(1000000)
        assert self.token.balance_of(self.second_address) == Wad(0)

    def test_transfer(self):
        # when
        self.token.transfer(self.second_address, Wad(500)).transact()

        # then
        assert self.token.balance_of(self.our_address) == Wad(999500)
        assert self.token.balance_of(self.second_address) == Wad(500)

    def test_transfer_async(self):
        # when
        synchronize([self.token.transfer(self.second_address, Wad(750)).transact_async()])

        # then
        assert self.token.balance_of(self.our_address) == Wad(999250)
        assert self.token.balance_of(self.second_address) == Wad(750)

    def test_allowance_of(self):
        assert self.token.allowance_of(self.our_address, self.second_address) == Wad(0)

    def test_approve(self):
        # when
        self.token.approve(self.second_address, Wad(2000)).transact()

        # then
        assert self.token.allowance_of(self.our_address, self.second_address) == Wad(2000)

    def test_equals(self):
        # given
        token1 = DSToken.deploy(self.web3, 'ABC')
        token2 = DSToken.deploy(self.web3, 'DEF')
        token2b = ERC20Token(web3=self.web3, address=token2.address)

        # expect
        assert token1 == token1
        assert token2 == token2b
        assert not token1 == token2
        assert not token1 == token2b

    def test_should_have_printable_representation(self):
        erc20token = ERC20Token(web3=self.web3, address=self.token.address)
        assert repr(erc20token) == f"ERC20Token('{erc20token.address}')"


class TestDSToken:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.dstoken = DSToken.deploy(self.web3, 'ABC')

    def test_authority(self):
        # given
        some_address = Address('0x4545454545676767676789898989890101010101')

        # when
        self.dstoken.set_authority(some_address).transact()

        # then
        assert self.dstoken.authority() == some_address

    def test_mint(self):
        # when
        self.dstoken.mint(Wad(100000)).transact()

        # then
        assert self.dstoken.balance_of(self.our_address) == Wad(100000)

    def test_burn(self):
        # given
        self.dstoken.mint(Wad(100000)).transact()

        # when
        self.dstoken.burn(Wad(40000)).transact()

        # then
        assert self.dstoken.balance_of(self.our_address) == Wad(60000)

    def test_should_have_printable_representation(self):
        assert repr(self.dstoken) == f"DSToken('{self.dstoken.address}')"


class TestDSEthToken:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.dsethtoken = DSEthToken.deploy(self.web3)

    def test_deposit(self):
        # when
        self.dsethtoken.deposit(Wad(100000)).transact()

        # then
        assert self.dsethtoken.balance_of(self.our_address) == Wad(100000)

    def test_withdraw(self):
        # given
        self.dsethtoken.deposit(Wad(100000)).transact()

        # when
        self.dsethtoken.withdraw(Wad(40000)).transact()

        # then
        assert self.dsethtoken.balance_of(self.our_address) == Wad(60000)

    def test_should_have_printable_representation(self):
        assert repr(self.dsethtoken) == f"DSEthToken('{self.dsethtoken.address}')"
