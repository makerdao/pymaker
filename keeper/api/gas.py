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


class GasPrice(object):
    def get_gas_price(self, time_elapsed: int) -> int:
        raise NotImplementedError("Please implement this method")


class FixedGasPrice(GasPrice):
    def __init__(self, gas_price: int):
        assert(isinstance(gas_price, int))
        self.gas_price = gas_price

    def get_gas_price(self, time_elapsed: int) -> int:
        assert(isinstance(time_elapsed, int))
        return self.gas_price


class IncreasingGasPrice(GasPrice):
    def __init__(self, initial_price: int, increase_by: int, every_secs: int):
        assert(isinstance(initial_price, int))
        assert(isinstance(increase_by, int))
        assert(isinstance(every_secs, int))
        assert(increase_by > 0)
        assert(every_secs > 0)
        self.initial_price = initial_price
        self.increase_by = increase_by
        self.every_secs = every_secs

    def get_gas_price(self, time_elapsed: int) -> int:
        assert(isinstance(time_elapsed, int))
        return self.initial_price + int(time_elapsed/self.every_secs)*self.increase_by
