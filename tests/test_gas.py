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
from typing import Optional, Tuple

from pymaker.gas import DefaultGasPrice, FixedGasPrice, GasStrategy, GeometricGasPrice, NodeAwareGasStrategy
from tests.conftest import patch_web3_block_data

GWEI = GasStrategy.GWEI


class TestGasPrice:
    def test_not_implemented(self):
        with pytest.raises(NotImplementedError):
            GasStrategy().get_gas_price(0)
        with pytest.raises(NotImplementedError):
            GasStrategy().get_gas_fees(0)

    def test_gwei(self):
        assert GasStrategy.GWEI == 1000000000


class TestDefaultGasPrice:
    def test_should_always_be_default(self):
        # given
        default_gas_price = DefaultGasPrice()

        # expect
        assert default_gas_price.get_gas_price(0) is None
        assert default_gas_price.get_gas_price(1) is None
        assert default_gas_price.get_gas_price(1000000) is None

        # expect
        assert default_gas_price.get_gas_fees(0) == (None, None)
        assert default_gas_price.get_gas_fees(1) == (None, None)
        assert default_gas_price.get_gas_fees(1000000) == (None, None)


class TestNodeAwareGasPrice:
    class DumbSampleImplementation(NodeAwareGasStrategy):
        def get_gas_price(self, time_elapsed: int) -> Optional[int]:
            return self.get_node_gas_price() * max(time_elapsed, 1)

        def get_gas_fees(self, time_elapsed: int) -> Optional[Tuple[int, int]]:
            return int(self.get_next_base_fee()*1.5), 2 * self.GWEI

    class BadImplementation(NodeAwareGasStrategy):
        pass

    def test_retrieve_node_gas_price(self, web3, mocker):
        strategy = TestNodeAwareGasPrice.DumbSampleImplementation(web3)
        assert strategy.get_gas_price(0) > 0
        assert strategy.get_gas_price(60) < strategy.get_gas_price(120)

        base_fee = 7 * GasStrategy.GWEI
        patch_web3_block_data(web3, mocker, base_fee)
        feecap, tip = strategy.get_gas_fees(90)
        assert feecap == base_fee * 1.5
        assert tip == 2 * GasStrategy.GWEI

    def test_not_implemented(self, web3):
        with pytest.raises(NotImplementedError):
            NodeAwareGasStrategy(web3)

        bad = TestNodeAwareGasPrice.BadImplementation(web3)
        with pytest.raises(NotImplementedError):
            bad.get_gas_price(0)
        with pytest.raises(NotImplementedError):
            bad.get_gas_fees(0)


class TestFixedGasPrice:
    def test_gas_price_should_stay_the_same(self):
        # given
        price = 9 * GasStrategy.GWEI
        feecap = 6 * GasStrategy.GWEI
        tip = 3 * GasStrategy.GWEI
        fixed_gas_price = FixedGasPrice(price, feecap, tip)

        # expect
        assert fixed_gas_price.get_gas_price(0) == price
        assert fixed_gas_price.get_gas_price(1) == price
        assert fixed_gas_price.get_gas_price(2) == price
        assert fixed_gas_price.get_gas_price(5) == price
        assert fixed_gas_price.get_gas_price(60) == price
        assert fixed_gas_price.get_gas_price(120) == price
        assert fixed_gas_price.get_gas_price(600) == price
        assert fixed_gas_price.get_gas_price(1000000) == price

        # expect
        assert fixed_gas_price.get_gas_fees(0) == (feecap, tip)
        assert fixed_gas_price.get_gas_fees(120) == (feecap, tip)
        assert fixed_gas_price.get_gas_fees(1000000) == (feecap, tip)

    def test_gas_price_should_be_updated_by_update_gas_price_method(self):
        # given
        price1 = 9 * GasStrategy.GWEI
        feecap1 = 6 * GasStrategy.GWEI
        tip1 = 3 * GasStrategy.GWEI
        price2 = 16 * GasStrategy.GWEI
        feecap2 = 10 * GasStrategy.GWEI
        tip2 = 2 * GasStrategy.GWEI

        # and
        fixed_gas_price = FixedGasPrice(price1, feecap1, tip1)

        # and
        assert fixed_gas_price.get_gas_price(0) == price1
        assert fixed_gas_price.get_gas_price(1) == price1
        assert fixed_gas_price.get_gas_price(2) == price1
        assert fixed_gas_price.get_gas_price(5) == price1
        assert fixed_gas_price.get_gas_fees(0) == (feecap1, tip1)
        assert fixed_gas_price.get_gas_fees(30) == (feecap1, tip1)

        # when
        fixed_gas_price.update_gas_price(price2, feecap2, tip2)

        # then
        assert fixed_gas_price.get_gas_price(60) == price2
        assert fixed_gas_price.get_gas_price(120) == price2
        assert fixed_gas_price.get_gas_price(600) == price2
        assert fixed_gas_price.get_gas_fees(90) == (feecap2, tip2)
        assert fixed_gas_price.get_gas_fees(360) == (feecap2, tip2)

    def test_gas_price_requires_type0_or_type2_params(self):
        with pytest.raises(AssertionError):
            FixedGasPrice(None, None, None)

        with pytest.raises(AssertionError):
            FixedGasPrice(None, 20 * GasStrategy.GWEI, None)
        with pytest.raises(AssertionError):
            FixedGasPrice(None, None, 1 * GasStrategy.GWEI)


class TestGeometricGasPrice:
    def test_gas_price_should_increase_with_time(self, web3, mocker):
        # given
        geometric_gas_price = GeometricGasPrice(web3=web3, initial_price=100, initial_tip=None, every_secs=10)

        # expect
        assert geometric_gas_price.get_gas_price(0) == 100
        assert geometric_gas_price.get_gas_price(1) == 100
        assert geometric_gas_price.get_gas_price(10) == 113
        assert geometric_gas_price.get_gas_price(15) == 113
        assert geometric_gas_price.get_gas_price(20) == 127
        assert geometric_gas_price.get_gas_price(30) == 143
        assert geometric_gas_price.get_gas_price(50) == 181
        assert geometric_gas_price.get_gas_price(100) == 325

        geometric_gas_price = GeometricGasPrice(web3=web3, initial_price=None, initial_tip=1 * GWEI, every_secs=10)
        patch_web3_block_data(web3, mocker, base_fee=10 * GWEI)
        last_fees = (0, 0)
        for i in [0, 10, 20, 30, 50, 100, 300, 1800, 3600]:
            current_fees = geometric_gas_price.get_gas_fees(i)
            assert current_fees[1] > last_fees[1]
            last_fees = current_fees

    def test_gas_price_should_obey_max_value(self, web3, mocker):
        # given
        max_price = 2500
        geometric_gas_price = GeometricGasPrice(web3=web3, initial_price=1000, initial_tip=10,
                                                every_secs=60, coefficient=1.125, max_price=max_price)
        patch_web3_block_data(web3, mocker, base_fee=10 * GWEI)

        # expect
        assert geometric_gas_price.get_gas_price(0) == 1000
        assert geometric_gas_price.get_gas_price(1) == 1000
        assert geometric_gas_price.get_gas_price(59) == 1000
        assert geometric_gas_price.get_gas_price(60) == 1125
        assert geometric_gas_price.get_gas_price(119) == 1125
        assert geometric_gas_price.get_gas_price(120) == 1266
        assert geometric_gas_price.get_gas_price(1200) == 2500
        assert geometric_gas_price.get_gas_price(3000) == 2500
        assert geometric_gas_price.get_gas_price(100000) == 2500
        # assert geometric_gas_price.get_gas_price(1000000) == 2500  # 277 hours produces overflow

        for i in [0, 120, 3600, 100000]:
            print(f"checking {i} seconds")
            current_fees = geometric_gas_price.get_gas_fees(i)
            assert current_fees[0] <= max_price
            assert current_fees[1] <= current_fees[0]

    @staticmethod
    def assert_gas_fees_equivalent(lhs: Tuple, rhs: Tuple, decimals=2):
        assert isinstance(lhs, Tuple)
        assert isinstance(rhs, Tuple)
        left_feecap = lhs[0] / GasStrategy.GWEI
        left_tip = lhs[1] / GasStrategy.GWEI
        right_feecap = rhs[0] / GasStrategy.GWEI
        right_tip = rhs[1] / GasStrategy.GWEI
        assert round(left_feecap, decimals) == round(right_feecap, decimals)
        assert round(left_tip, decimals) == round(right_tip, decimals)

    def test_behaves_with_realistic_values(self, web3, mocker):
        # given
        GWEI = 1000000000
        base_fee = 50*GWEI
        geometric_gas_price = GeometricGasPrice(web3=web3, initial_price=100*GWEI, initial_tip=15*GWEI,
                                                every_secs=10, coefficient=1.25, max_price=4000*GWEI)
        patch_web3_block_data(web3, mocker, base_fee)

        # See gas sandbox spreadsheet in test folder to validate calculations

        assert round(geometric_gas_price.get_gas_price(0) / GWEI, 1) == 100.0
        assert round(geometric_gas_price.get_gas_price(1) / GWEI, 1) == 100.0
        assert round(geometric_gas_price.get_gas_price(10) / GWEI, 1) == 125.0
        assert round(geometric_gas_price.get_gas_price(12) / GWEI, 1) == 125.0
        assert round(geometric_gas_price.get_gas_price(30) / GWEI, 1) == 195.3
        assert round(geometric_gas_price.get_gas_price(60) / GWEI, 1) == 381.5
        assert round(geometric_gas_price.get_gas_price(180) / GWEI, 1) == 4000.0

        self.assert_gas_fees_equivalent(geometric_gas_price.get_gas_fees(0), (75 * GWEI, 15 * GWEI))
        self.assert_gas_fees_equivalent(geometric_gas_price.get_gas_fees(30), (146.48 * GWEI, 29.30 * GWEI))
        self.assert_gas_fees_equivalent(geometric_gas_price.get_gas_fees(60), (286.10 * GWEI, 57.22 * GWEI))
        self.assert_gas_fees_equivalent(geometric_gas_price.get_gas_fees(300), (4000 * GWEI, 4000 * GWEI))

    def test_should_require_positive_initial_price(self, web3):
        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, 0, None, 60)
        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, None, 0, 0, 60)

        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, -1, None, 60)
        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, None, -1, -1, 60)

    def test_should_require_positive_every_secs_value(self, web3):
        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, 1000, None, 0)
        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, None, 600, 50, 0)

        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, 1000, None, -1)
        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, None, 600, 50, -1)

    def test_should_require_positive_coefficient(self, web3):
        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, 1000, 600, 50, 60, 0)

        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, 1000, 600, 50, 60, 1)

        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, 1000, 600, 50, 60, -1)

    def test_should_require_positive_max_price_if_provided(self, web3):
        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, 1000, 50, 60, 1.125, 0)

        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, 1000, 50, 60, 1.125, -1)

    def test_max_price_should_exceed_initial_price(self, web3):
        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, 6000, 50, 30, 2.25, 5000)

        with pytest.raises(AssertionError):
            GeometricGasPrice(web3, None, 201, 30, 1.424, 200)
