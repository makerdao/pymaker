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

from pymaker.logger import Logger
from pymaker.gas import DefaultGasPrice, FixedGasPrice, IncreasingGasPrice, GasPrice, GasPriceFile


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


class TestGasPriceFile:
    logger = Logger('-', '-')

    @staticmethod
    def config_file(body, tmpdir):
        file = tmpdir.join("gas_price.json")
        file.write(body)
        return str(file)

    def test_can_behave_as_default_gas_price(self, tmpdir):
        # given
        file = self.config_file("""{}""", tmpdir)
        file_gas_price = GasPriceFile(file, self.logger)

        # expect
        assert file_gas_price.get_gas_price(0) is None
        assert file_gas_price.get_gas_price(1) is None
        assert file_gas_price.get_gas_price(1000000) is None

    def test_can_behave_as_fixed_gas_price(self, tmpdir):
        # given
        file = self.config_file("""{"gasPrice": 7000000000}""", tmpdir)
        file_gas_price = GasPriceFile(file, self.logger)

        # expect
        assert file_gas_price.get_gas_price(0) == 7000000000
        assert file_gas_price.get_gas_price(1) == 7000000000
        assert file_gas_price.get_gas_price(1000000) == 7000000000

    def test_can_behave_as_increasing_gas_price_without_max(self, tmpdir):
        # given
        file = self.config_file("""{
            "gasPrice": 7000000000,
            "gasPriceIncrease": 1000000000,
            "gasPriceIncreaseEvery": 60}""", tmpdir)
        file_gas_price = GasPriceFile(file, self.logger)

        # expect
        assert file_gas_price.get_gas_price(0) == 7000000000
        assert file_gas_price.get_gas_price(1) == 7000000000
        assert file_gas_price.get_gas_price(59) == 7000000000
        assert file_gas_price.get_gas_price(60) == 8000000000
        assert file_gas_price.get_gas_price(119) == 8000000000
        assert file_gas_price.get_gas_price(120) == 9000000000
        assert file_gas_price.get_gas_price(1200) == 27000000000

    def test_can_behave_as_increasing_gas_price_with_max(self, tmpdir):
        # given
        file = self.config_file("""{
            "gasPrice": 7000000000,
            "gasPriceIncrease": 1000000000,
            "gasPriceIncreaseEvery": 60,
            "gasPriceMax": 12000000000}""", tmpdir)
        file_gas_price = GasPriceFile(file, self.logger)

        # expect
        assert file_gas_price.get_gas_price(0) == 7000000000
        assert file_gas_price.get_gas_price(1) == 7000000000
        assert file_gas_price.get_gas_price(59) == 7000000000
        assert file_gas_price.get_gas_price(60) == 8000000000
        assert file_gas_price.get_gas_price(119) == 8000000000
        assert file_gas_price.get_gas_price(120) == 9000000000
        assert file_gas_price.get_gas_price(1200) == 12000000000
