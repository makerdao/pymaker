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

from pymaker.gas import DefaultGasPrice, FixedGasPrice, GasPrice, GeometricGasPrice, IncreasingGasPrice


class TestGasPrice:
    def test_not_implemented(self):
        with pytest.raises(Exception):
            GasPrice().get_gas_price(0)


class TestDefaultGasPrice:
    def test_should_always_be_default(self):
        # given
        default_gas_price = DefaultGasPrice()

        # expect
        assert default_gas_price.get_gas_price(0) is None
        assert default_gas_price.get_gas_price(1) is None
        assert default_gas_price.get_gas_price(1000000) is None


class TestFixedGasPrice:
    def test_gas_price_should_stay_the_same(self):
        # given
        value = 9000000000
        fixed_gas_price = FixedGasPrice(value)

        # expect
        assert fixed_gas_price.get_gas_price(0) == value
        assert fixed_gas_price.get_gas_price(1) == value
        assert fixed_gas_price.get_gas_price(2) == value
        assert fixed_gas_price.get_gas_price(5) == value
        assert fixed_gas_price.get_gas_price(60) == value
        assert fixed_gas_price.get_gas_price(120) == value
        assert fixed_gas_price.get_gas_price(600) == value
        assert fixed_gas_price.get_gas_price(1000000) == value

    def test_gas_price_should_be_updated_by_update_gas_price_method(self):
        # given
        value1 = 9000000000
        value2 = 16000000000

        # and
        fixed_gas_price = FixedGasPrice(value1)

        # and
        assert fixed_gas_price.get_gas_price(0) == value1
        assert fixed_gas_price.get_gas_price(1) == value1
        assert fixed_gas_price.get_gas_price(2) == value1
        assert fixed_gas_price.get_gas_price(5) == value1

        # when
        fixed_gas_price.update_gas_price(value2)

        # then
        assert fixed_gas_price.get_gas_price(60) == value2
        assert fixed_gas_price.get_gas_price(120) == value2
        assert fixed_gas_price.get_gas_price(600) == value2


class TestIncreasingGasPrice:
    def test_gas_price_should_increase_with_time(self):
        # given
        increasing_gas_price = IncreasingGasPrice(1000, 100, 60, None)

        # expect
        assert increasing_gas_price.get_gas_price(0) == 1000
        assert increasing_gas_price.get_gas_price(1) == 1000
        assert increasing_gas_price.get_gas_price(59) == 1000
        assert increasing_gas_price.get_gas_price(60) == 1100
        assert increasing_gas_price.get_gas_price(119) == 1100
        assert increasing_gas_price.get_gas_price(120) == 1200
        assert increasing_gas_price.get_gas_price(1200) == 3000

    def test_gas_price_should_obey_max_value(self):
        # given
        increasing_gas_price = IncreasingGasPrice(1000, 100, 60, 2500)

        # expect
        assert increasing_gas_price.get_gas_price(0) == 1000
        assert increasing_gas_price.get_gas_price(1) == 1000
        assert increasing_gas_price.get_gas_price(59) == 1000
        assert increasing_gas_price.get_gas_price(60) == 1100
        assert increasing_gas_price.get_gas_price(119) == 1100
        assert increasing_gas_price.get_gas_price(120) == 1200
        assert increasing_gas_price.get_gas_price(1200) == 2500
        assert increasing_gas_price.get_gas_price(3000) == 2500
        assert increasing_gas_price.get_gas_price(1000000) == 2500

    def test_should_require_positive_initial_price(self):
        with pytest.raises(Exception):
            IncreasingGasPrice(0, 1000, 60, None)

        with pytest.raises(Exception):
            IncreasingGasPrice(-1, 1000, 60, None)

    def test_should_require_positive_increase_by_value(self):
        with pytest.raises(Exception):
            IncreasingGasPrice(1000, 0, 60, None)

        with pytest.raises(Exception):
            IncreasingGasPrice(1000, -1, 60, None)

    def test_should_require_positive_every_secs_value(self):
        with pytest.raises(Exception):
            IncreasingGasPrice(1000, 100, 0, None)

        with pytest.raises(Exception):
            IncreasingGasPrice(1000, 100, -1, None)

    def test_should_require_positive_max_price_if_provided(self):
        with pytest.raises(Exception):
            IncreasingGasPrice(1000, 1000, 60, 0)

        with pytest.raises(Exception):
            IncreasingGasPrice(1000, 1000, 60, -1)


class TestGeometricGasPrice:
    def test_gas_price_should_increase_with_time(self):
        # given
        geometric_gas_price = GeometricGasPrice(100, 10)

        # expect
        assert geometric_gas_price.get_gas_price(0) == 100
        assert geometric_gas_price.get_gas_price(1) == 100
        assert geometric_gas_price.get_gas_price(10) == 113
        assert geometric_gas_price.get_gas_price(15) == 113
        assert geometric_gas_price.get_gas_price(20) == 127
        assert geometric_gas_price.get_gas_price(30) == 143
        assert geometric_gas_price.get_gas_price(50) == 181
        assert geometric_gas_price.get_gas_price(100) == 325

    def test_gas_price_should_obey_max_value(self):
        # given
        geometric_gas_price = GeometricGasPrice(1000, 60, 1.125, 2500)

        # expect
        assert geometric_gas_price.get_gas_price(0) == 1000
        assert geometric_gas_price.get_gas_price(1) == 1000
        assert geometric_gas_price.get_gas_price(59) == 1000
        assert geometric_gas_price.get_gas_price(60) == 1125
        assert geometric_gas_price.get_gas_price(119) == 1125
        assert geometric_gas_price.get_gas_price(120) == 1266
        assert geometric_gas_price.get_gas_price(1200) == 2500
        assert geometric_gas_price.get_gas_price(3000) == 2500
        assert geometric_gas_price.get_gas_price(1000000) == 2500

    def test_behaves_with_realistic_values(self):
        # given
        GWEI = 1000000000
        geometric_gas_price = GeometricGasPrice(100*GWEI, 10, 1+(0.125*2))

        for seconds in [0,1,10,12,30,60]:
            print(f"gas price after {seconds} seconds is {geometric_gas_price.get_gas_price(seconds)/GWEI}")

        assert round(geometric_gas_price.get_gas_price(0) / GWEI, 1) == 100.0
        assert round(geometric_gas_price.get_gas_price(1) / GWEI, 1) == 100.0
        assert round(geometric_gas_price.get_gas_price(10) / GWEI, 1) == 125.0
        assert round(geometric_gas_price.get_gas_price(12) / GWEI, 1) == 125.0
        assert round(geometric_gas_price.get_gas_price(30) / GWEI, 1) == 195.3
        assert round(geometric_gas_price.get_gas_price(60) / GWEI, 1) == 381.5

    def test_should_require_positive_initial_price(self):
        with pytest.raises(AssertionError):
            GeometricGasPrice(0, 60)

        with pytest.raises(AssertionError):
            GeometricGasPrice(-1, 60)

    def test_should_require_positive_every_secs_value(self):
        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 0)

        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, -1)

    def test_should_require_positive_coefficient(self):
        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 60, 0)

        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 60, 1)

        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 60, -1)

    def test_should_require_positive_max_price_if_provided(self):
        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 60, 1.125, 0)

        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 60, 1.125, -1)
