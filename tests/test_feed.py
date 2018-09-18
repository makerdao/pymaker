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
from pymaker.feed import DSValue


class TestDSValue:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.dsvalue = DSValue.deploy(self.web3)

    def test_fail_when_no_contract_under_that_address(self):
        # expect
        with pytest.raises(Exception):
            DSValue(web3=self.web3, address=Address('0xdeadadd1e5500000000000000000000000000000'))

    def test_address(self):
        assert isinstance(self.dsvalue.address, Address)

    def test_no_value_after_deploy(self):
        # expect
        assert self.dsvalue.has_value() is False
        with pytest.raises(Exception):
            self.dsvalue.read()
        with pytest.raises(Exception):
            self.dsvalue.read_as_int()
        with pytest.raises(Exception):
            self.dsvalue.read_as_hex()

    def test_poke(self):
        # when
        self.dsvalue.poke(bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0xf4])).transact()

        # then
        assert self.dsvalue.has_value() is True
        assert self.dsvalue.read_as_int() == 500
        assert self.dsvalue.read() == bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0xf4])

    def test_poke_with_int(self):
        # when
        self.dsvalue.poke_with_int(500).transact()

        # then
        assert self.dsvalue.has_value() is True
        assert self.dsvalue.read_as_int() == 500
        assert self.dsvalue.read() == bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0xf4])

    def test_void(self):
        # given
        self.dsvalue.poke_with_int(250).transact()
        assert self.dsvalue.has_value() is True

        # when
        self.dsvalue.void().transact()

        # then
        assert self.dsvalue.has_value() is False

    def test_should_have_printable_representation(self):
        assert repr(self.dsvalue) == f"DSValue('{self.dsvalue.address}')"
