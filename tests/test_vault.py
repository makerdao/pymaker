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

import pytest
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.vault import DSVault


class TestDSVault:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.dsvault = DSVault.deploy(self.web3)

    def test_fail_when_no_contract_under_that_address(self):
        # expect
        with pytest.raises(Exception):
            DSVault(web3=self.web3, address=Address('0xdeadadd1e5500000000000000000000000000000'))

    def test_authority(self):
        # given
        some_address = Address('0x0000000000111111111122222222223333333333')

        # when
        self.dsvault.set_authority(some_address).transact()

        # then
        assert self.dsvault.authority() == some_address

    def test_should_have_printable_representation(self):
        assert repr(self.dsvault) == f"DSVault('{self.dsvault.address}')"
