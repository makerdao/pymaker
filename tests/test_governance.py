# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 EdNoepel
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
from pymaker.auth import DSAuth
from pymaker.governance import DSPause
from datetime import datetime, timedelta


@pytest.mark.skip(reason="not fully implemented")
class TestDSPause:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)

        ds_auth = DSAuth.deploy(self.web3)
        self.ds_pause = DSPause.deploy(self.web3, 5, self.our_address, ds_auth)

        self.plan = DSPause.Plan(usr=self.our_address,
                                 fax=self.web3.toBytes(text='abi.encodeWithSignature("sig()")'),
                                 eta=(datetime.utcnow() + timedelta(seconds=10)))

    def test_drop(self):
        # assert self.ds_pause.plot(self.plan).transact()
        assert self.ds_pause.drop(self.plan).transact()

    def test_exec(self):
        # assert self.ds_pause.plot(self.plan).transact()
        assert self.ds_pause.exec(self.plan).transact()
