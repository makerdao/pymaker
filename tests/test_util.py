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
import time
from unittest.mock import Mock, call

import pytest
from web3 import Web3

from pymaker import Address
from pymaker.util import synchronize, int_to_bytes32, bytes_to_int, bytes_to_hexstring, hexstring_to_bytes, \
    AsyncCallback, chain


async def async_return(result):
    return result


async def async_exception():
    await asyncio.sleep(0.1)
    raise Exception("Exception to be passed further down")


def mocked_web3(block_0_hash: str) -> Web3:
    def side_effect(block_number):
        if block_number == 0:
            return {'hash': block_0_hash}
        else:
            raise Exception("Unknown block number queried")

    web3 = Mock(Web3)
    web3.eth = Mock()
    web3.eth.getBlock = Mock(side_effect=side_effect)
    return web3


def test_chain_should_recognize_ethlive():
    # given
    web3 = mocked_web3(block_0_hash="0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3")

    # expect
    assert chain(web3) == "ethlive"


def test_chain_should_recognize_kovan():
    # given
    web3 = mocked_web3(block_0_hash="0xa3c565fc15c7478862d50ccd6561e3c06b24cc509bf388941c25ea985ce32cb9")

    # expect
    assert chain(web3) == "kovan"


def test_chain_should_recognize_ropsten():
    # given
    web3 = mocked_web3(block_0_hash="0x41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d")

    # expect
    assert chain(web3) == "ropsten"


def test_chain_should_recognize_morden():
    # given
    web3 = mocked_web3(block_0_hash="0x0cd786a2425d16f152c658316c423e6ce1181e15c3295826d7c9904cba9ce303")

    # expect
    assert chain(web3) == "morden"


def test_chain_should_report_unknown_chains_as_unknown():
    # given
    web3 = mocked_web3(block_0_hash="0x0000000000011111111222222333333333333555555555555666666444444333")

    # expect
    assert chain(web3) == "unknown"


def mocked_web3_transaction_count(address: Address, latest: int, pending: int) -> Web3:
    def side_effect(param_address, param_mode):
        assert param_address == address.address
        if param_mode == 'latest':
            return latest
        elif param_mode == 'pending':
            return pending
        else:
            raise Exception("Unknown mode")

    web3 = Mock(Web3)
    web3.eth = Mock()
    web3.eth.getTransactionCount = Mock(side_effect=side_effect)
    return web3


def test_synchronize_should_return_empty_list_for_no_futures():
    assert synchronize([]) == []


def test_synchronize_should_return_results_of_all_async_calls():
    assert synchronize([async_return(1)]) == [1]
    assert synchronize([async_return(1), async_return(2)]) == [1, 2]
    assert synchronize([async_return(1), async_return(2), async_return(3)]) == [1, 2, 3]


def test_synchronize_should_pass_exceptions():
    with pytest.raises(Exception):
        synchronize([async_return(1), async_exception(), async_return(3)])


def test_int_to_bytes32():
    assert int_to_bytes32(0) == bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    assert int_to_bytes32(1) == bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01])

    assert int_to_bytes32(512) == bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00])
    
    assert int_to_bytes32(2**256-1) == bytes([0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                                              0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                                              0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                                              0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff])


def test_bytes_to_int():
    assert bytes_to_int(bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])) == 0

    assert bytes_to_int(bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01])) == 1

    assert bytes_to_int(bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01])) == 257

    assert bytes_to_int(bytes([0x00])) == 0

    assert bytes_to_int(bytes([0x01, 0x01])) == 257

    assert bytes_to_int(bytes([0x00, 0x01, 0x01])) == 257

    assert bytes_to_int(bytes([0x00, 0x00, 0x01, 0x01])) == 257

    assert bytes_to_int(bytes([0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                               0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                               0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                               0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff])) == 2**256-1


def test_bytes_to_int_from_string():
    assert bytes_to_int('\x00') == 0
    assert bytes_to_int('\x01') == 1
    assert bytes_to_int('\x01\x01') == 257
    assert bytes_to_int('\x00\x01\x01') == 257
    assert bytes_to_int('\x00\x00\x01\x01') == 257


def test_bytes_to_int_from_int_should_fail():
    with pytest.raises(AssertionError):
        bytes_to_int(0)


def test_bytes_to_hexstring():
    assert bytes_to_hexstring(bytes([0x00])) == '0x00'
    assert bytes_to_hexstring(bytes([0x01, 0x02, 0x03])) == '0x010203'
    assert bytes_to_hexstring(bytes([0xff, 0xff])) == '0xffff'


def test_hexstring_to_bytes():
    assert hexstring_to_bytes('0x00') == bytes([0x00])
    assert hexstring_to_bytes('0x010203') == bytes([0x01, 0x02, 0x03])
    assert hexstring_to_bytes('0xffff') == bytes([0xff, 0xff])


class TestAsyncCallback:
    @pytest.fixture
    def callbacks(self):
        class Callbacks:
            counter = 0

            def short_running_callback(self):
                self.counter += 1

            def long_running_callback(self):
                time.sleep(1)
                self.counter += 1

        return Callbacks()

    def test_should_call_callback(self, callbacks):
        # given
        async_callback = AsyncCallback(callbacks.short_running_callback)

        # when
        result = async_callback.trigger()

        # then
        assert result
        assert callbacks.counter == 1

    def test_should_not_call_callback_if_previous_one_is_still_running(self, callbacks):
        # given
        async_callback = AsyncCallback(callbacks.long_running_callback)

        # when
        result1 = async_callback.trigger()
        result2 = async_callback.trigger()

        # and
        time.sleep(2)

        # then
        assert result1
        assert not result2
        assert callbacks.counter == 1

    def test_should_call_callback_again_if_previous_one_is_finished(self, callbacks):
        # given
        async_callback = AsyncCallback(callbacks.long_running_callback)

        # when
        result1 = async_callback.trigger()
        time.sleep(2)

        # and
        result2 = async_callback.trigger()
        time.sleep(2)

        # then
        assert result1
        assert result2
        assert callbacks.counter == 2

    def test_should_wait_for_the_callback_to_finish(self, callbacks):
        # given
        async_callback = AsyncCallback(callbacks.long_running_callback)
        async_callback.trigger()
        assert callbacks.counter == 0

        # when
        async_callback.wait()

        # then
        assert callbacks.counter == 1

    def test_should_call_on_start_and_on_finish_before_and_after_the_callback(self, callbacks):
        # given
        mock = Mock()
        on_start = mock.on_start
        callback = mock.callback
        on_finish = mock.on_finish

        # when
        async_callback = AsyncCallback(callback)
        async_callback.trigger(on_start, on_finish)

        # then
        assert mock.mock_calls == [call.on_start(), call.callback(), call.on_finish()]
