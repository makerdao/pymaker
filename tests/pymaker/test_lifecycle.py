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
from mock import MagicMock
from web3 import EthereumTesterProvider, Web3

from pymaker import Address, Logger
from pymaker.lifecycle import Web3Lifecycle


class TestLifecycle:
    def setup_method(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)
        self.logger = Logger('-', '-')

    def test_should_always_exit(self):
        with pytest.raises(SystemExit):
            with Web3Lifecycle(self.web3, self.logger):
                pass

    def test_should_call_startup_callback(self):
        # given
        startup_mock = MagicMock()

        # when
        with pytest.raises(SystemExit):
            with Web3Lifecycle(self.web3, self.logger) as lifecycle:
                lifecycle.on_startup(startup_mock)

        # then
        startup_mock.assert_called()

    def test_should_fail_to_register_two_startup_callbacks(self):
        # expect
        with pytest.raises(BaseException):
            with Web3Lifecycle(self.web3, self.logger) as lifecycle:
                lifecycle.on_startup(lambda: 1)
                lifecycle.on_startup(lambda: 2)

    def test_should_call_shutdown_callback(self):
        # given
        ordering = []
        startup_mock = MagicMock(side_effect=lambda: ordering.append('STARTUP'))
        shutdown_mock = MagicMock(side_effect=lambda: ordering.append('SHUTDOWN'))

        # when
        with pytest.raises(SystemExit):
            with Web3Lifecycle(self.web3, self.logger) as lifecycle:
                lifecycle.on_startup(startup_mock)
                lifecycle.on_shutdown(shutdown_mock)

        # then
        assert ordering == ['STARTUP', 'SHUTDOWN']

    def test_should_fail_to_register_two_shutdown_callbacks(self):
        # expect
        with pytest.raises(BaseException):
            with Web3Lifecycle(self.web3, self.logger) as lifecycle:
                lifecycle.on_shutdown(lambda: 1)
                lifecycle.on_shutdown(lambda: 2)

    def test_every(self):
        self.counter = 0

        def callback():
            self.counter = self.counter + 1
            if self.counter >= 2:
                lifecycle.terminate("Unit test is over")

        # given
        mock = MagicMock(side_effect=callback)

        # when
        with pytest.raises(SystemExit):
            with Web3Lifecycle(self.web3, self.logger) as lifecycle:
                lifecycle.every(1, mock)

        # then
        assert mock.call_count >= 2
        assert lifecycle.terminated_internally
