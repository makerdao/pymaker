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
from datetime import datetime, timedelta
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.auth import DSGuard, DSAuth, DSPause
from pymaker.util import hexstring_to_bytes


class TestDSGuard:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.ds_guard = DSGuard.deploy(self.web3)

    def can_call(self, src: str, dst: str, sig: str) -> bool:
        return self.ds_guard._contract.call().canCall(src, dst, hexstring_to_bytes(sig))

    def test_fail_when_no_contract_under_that_address(self):
        # expect
        with pytest.raises(Exception):
            DSGuard(web3=self.web3, address=Address('0xdeadadd1e5500000000000000000000000000000'))

    def test_no_permit_by_default(self):
        # expect
        assert not self.can_call(src='0x1111111111222222222211111111112222222222',
                                 dst='0x3333333333444444444433333333334444444444',
                                 sig='0xab121fd7')

    def test_permit_any_to_any_with_any_sig(self):
        # when
        self.ds_guard.permit(DSGuard.ANY, DSGuard.ANY, DSGuard.ANY).transact()

        # then
        assert self.can_call(src='0x1111111111222222222211111111112222222222',
                             dst='0x3333333333444444444433333333334444444444',
                             sig='0xab121fd7')

    def test_permit_specific_addresses_and_sig(self):
        # when
        self.ds_guard.permit(src=Address('0x1111111111222222222211111111112222222222'),
                             dst=Address('0x3333333333444444444433333333334444444444'),
                             sig=hexstring_to_bytes('0xab121fd7')).transact()

        # then
        assert self.can_call(src='0x1111111111222222222211111111112222222222',
                             dst='0x3333333333444444444433333333334444444444',
                             sig='0xab121fd7')

        # and
        assert not self.can_call(src='0x3333333333444444444433333333334444444444',
                                 dst='0x1111111111222222222211111111112222222222',
                                 sig='0xab121fd7')  # different addresses
        assert not self.can_call(src='0x1111111111222222222211111111112222222222',
                                 dst='0x3333333333444444444433333333334444444444',
                                 sig='0xab121fd8')  # different sig


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

    @pytest.mark.skip(reason="transaction fails on ganache")
    def test_drop(self):
        # assert self.ds_pause.plot(self.plan).transact()
        assert self.ds_pause.drop(self.plan).transact()

    @pytest.mark.skip(reason="transaction fails on ganache")
    def test_exec(self):
        # assert self.ds_pause.plot(self.plan).transact()
        assert self.ds_pause.exec(self.plan).transact()
