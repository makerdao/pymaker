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

from unittest.mock import Mock

from web3 import Web3


def is_hashable(v):
    """Determine whether `v` can be hashed."""
    try:
        hash(v)
    except TypeError:
        return False
    return True


def wait_until_mock_called(mock: Mock):
    while not mock.called:
        pass
    return mock.call_args[0]


def time_travel_by(web3: Web3, seconds: int):
    assert(isinstance(web3, Web3))
    assert(isinstance(seconds, int))

    web3.manager.request_blocking("evm_increaseTime", [seconds])

def snapshot(web3: Web3):
    assert(isinstance(web3, Web3))

    return web3.manager.request_blocking("evm_snapshot", [])

def reset(web3: Web3, snap_id):
    assert(isinstance(web3, Web3))

    return web3.manager.request_blocking("evm_revert", [snap_id])
