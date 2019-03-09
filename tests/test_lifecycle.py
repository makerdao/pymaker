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

import time
from threading import Event
from unittest.mock import Mock

import pytest
from mock import MagicMock
from web3 import Web3, HTTPProvider

import pymaker
from pymaker import Address
from pymaker.lifecycle import Lifecycle, trigger_event


@pytest.mark.timeout(60)
class TestLifecycle:
    def setup_method(self):
        self.web3 = Web3(HTTPProvider("http://localhost:8555"))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.our_address = Address(self.web3.eth.defaultAccount)

        # `test_etherdelta.py` executes before this test file and creates some event filters,
        # so we need to clear the list of filter threads as otherwise `Web3Lifecycle` will
        # be waiting forever for them to terminate and the test harness will never finish
        pymaker.filter_threads = []

    def use_web3(self, with_web3: bool):
        return self.web3 if with_web3 else None

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_always_exit(self, with_web3):
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)):
                pass

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_start_instantly_if_no_initial_delay(self, with_web3):
        # given
        start_time = int(time.time())

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                pass

        # then
        end_time = int(time.time())
        assert end_time - start_time <= 2

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_obey_initial_delay(self, with_web3):
        # given
        start_time = int(time.time())

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.initial_delay(5)

        # then
        end_time = int(time.time())
        assert end_time - start_time >= 4

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_check_initial_checks(self, with_web3):
        # given
        check_1 = Mock(return_value=True)
        check_2 = Mock(return_value=True)

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.wait_for(check_1, 5)
                lifecycle.wait_for(check_2, 5)

        # then
        assert check_1.call_count == 1
        assert check_2.call_count == 1

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_time_out_initial_checks_even_if_they_constantly_return_false(self, with_web3):
        # given
        start_time = int(time.time())

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.wait_for(lambda: False, 5)

        # then
        end_time = int(time.time())
        assert end_time - start_time >= 4

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_call_startup_callback(self, with_web3):
        # given
        startup_mock = MagicMock()

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.on_startup(startup_mock)

        # then
        startup_mock.assert_called()

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_fail_to_register_two_startup_callbacks(self, with_web3):
        # expect
        with pytest.raises(BaseException):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.on_startup(lambda: 1)
                lifecycle.on_startup(lambda: 2)

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_call_shutdown_callback(self, with_web3):
        # given
        ordering = []
        startup_mock = MagicMock(side_effect=lambda: ordering.append('STARTUP'))
        shutdown_mock = MagicMock(side_effect=lambda: ordering.append('SHUTDOWN'))

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.on_startup(startup_mock)
                lifecycle.on_shutdown(shutdown_mock)

        # then
        assert ordering == ['STARTUP', 'SHUTDOWN']

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_fail_to_register_two_shutdown_callbacks(self, with_web3):
        # expect
        with pytest.raises(BaseException):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.on_shutdown(lambda: 1)
                lifecycle.on_shutdown(lambda: 2)

    def test_should_fail_to_register_two_block_callbacks(self):
        # expect
        with pytest.raises(BaseException):
            with Lifecycle(self.web3) as lifecycle:
                lifecycle.on_block(lambda: 1)
                lifecycle.on_block(lambda: 2)

    def test_should_fail_to_register_block_callback_if_no_web3(self):
        # expect
        with pytest.raises(BaseException):
            with Lifecycle() as lifecycle:
                lifecycle.on_block(lambda: 1)

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_every(self, with_web3):
        self.counter = 0

        def callback():
            self.counter = self.counter + 1
            if self.counter >= 2:
                lifecycle.terminate("Unit test is over")

        # given
        mock = MagicMock(side_effect=callback)

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.every(1, mock)

        # then
        assert mock.call_count >= 2
        assert lifecycle.terminated_internally

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_on_event_fires_whenever_event_triggered(self, with_web3):
        event = Event()
        self.counter = 0

        def every_callback():
            self.counter = self.counter + 1
            trigger_event(event)
            if self.counter >= 2:
                time.sleep(1)
                lifecycle.terminate("Unit test is over")

        # given
        mock = Mock()

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.every(1, every_callback)
                lifecycle.on_event(event, 9999, mock)

        # then
        assert mock.call_count >= 2
        assert lifecycle.terminated_internally

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_on_event_fires_every_min_frequency_if_event_not_triggered(self, with_web3):
        self.counter = 0

        def callback():
            self.counter = self.counter + 1
            if self.counter >= 2:
                lifecycle.terminate("Unit test is over")

        # given
        mock = MagicMock(side_effect=callback)

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.on_event(Event(), 1, mock)

        # then
        assert mock.call_count >= 2
        assert lifecycle.terminated_internally

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_every_does_not_start_operating_until_startup_callback_is_finished(self, with_web3):
        # given
        self.every_triggered = False

        def startup_callback():
            time.sleep(3)
            assert not self.every_triggered

        def every_callback():
            self.every_triggered = True
            lifecycle.terminate("Unit test is over")

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.on_startup(startup_callback)
                lifecycle.every(1, every_callback)

        # then
        assert self.every_triggered

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_event_does_not_start_operating_until_startup_callback_is_finished(self, with_web3):
        # given
        self.event_triggered = False

        def startup_callback():
            time.sleep(3)
            assert not self.event_triggered

        def event_callback():
            self.event_triggered = True
            lifecycle.terminate("Unit test is over")

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.on_startup(startup_callback)
                lifecycle.on_event(Event(), 1, event_callback)

        # then
        assert self.event_triggered

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_every_should_not_fire_when_keeper_is_already_terminating(self, with_web3):
        # given
        self.every_counter = 0

        def shutdown_callback():
            time.sleep(5)

        def every_callback():
            self.every_counter = self.every_counter + 1
            lifecycle.terminate("Unit test is over")

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.every(1, every_callback)
                lifecycle.on_shutdown(shutdown_callback)

        # then
        assert self.every_counter <= 2

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_events_should_not_fire_when_keeper_is_already_terminating(self, with_web3):
        # given
        self.event_counter = 0

        def shutdown_callback():
            time.sleep(5)

        def event_callback():
            self.event_counter = self.event_counter + 1
            lifecycle.terminate("Unit test is over")

        # when
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.on_event(Event(), 1, event_callback)
                lifecycle.on_shutdown(shutdown_callback)

        # then
        assert self.event_counter <= 2

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_not_call_shutdown_until_every_timer_has_finished(self, with_web3):
        # given
        self.every1_finished = False
        self.every2_finished = False

        def shutdown_callback():
            assert self.every1_finished
            assert self.every2_finished

        def every_callback_1():
            time.sleep(1)
            lifecycle.terminate("Unit test is over")
            time.sleep(4)
            self.every1_finished = True

        def every_callback_2():
            time.sleep(2)
            self.every2_finished = True

        # expect
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.every(1, every_callback_1)
                lifecycle.every(1, every_callback_2)
                lifecycle.on_shutdown(shutdown_callback)  # assertions are in `shutdown_callback`

    @pytest.mark.parametrize('with_web3', [False, True])
    def test_should_not_call_shutdown_until_every_event_has_finished(self, with_web3):
        # given
        self.event1_finished = False
        self.event2_finished = False

        def shutdown_callback():
            assert self.event1_finished
            assert self.event2_finished

        def event_callback_1():
            time.sleep(1)
            lifecycle.terminate("Unit test is over")
            time.sleep(4)
            self.event1_finished = True

        def event_callback_2():
            time.sleep(2)
            self.event2_finished = True

        # expect
        with pytest.raises(SystemExit):
            with Lifecycle(self.use_web3(with_web3)) as lifecycle:
                lifecycle.on_event(Event(), 1, event_callback_1)
                lifecycle.on_event(Event(), 1, event_callback_2)
                lifecycle.on_shutdown(shutdown_callback)  # assertions are in `shutdown_callback`
