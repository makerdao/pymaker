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
import asyncio

import pytest

from api.util import synchronize


async def async_return(result):
    return result


async def async_exception():
    await asyncio.sleep(0.1)
    raise Exception("Exception to be passed further down")


def test_synchronize_should_return_empty_list_for_no_futures():
    assert synchronize([]) == []


def test_synchronize_should_return_results_of_all_async_calls():
    assert synchronize([async_return(1)]) == [1]
    assert synchronize([async_return(1), async_return(2)]) == [1, 2]
    assert synchronize([async_return(1), async_return(2), async_return(3)]) == [1, 2, 3]


def test_synchronize_should_pass_exceptions():
    with pytest.raises(Exception):
        synchronize([async_return(1), async_exception(), async_return(3)])
