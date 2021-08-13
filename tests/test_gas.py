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
from web3 import Web3
from web3._utils.events import AttributeDict

from pymaker.gas import DefaultGasPrice, FixedGasPrice, GasStrategy, GeometricGasPrice, NodeAwareGasStrategy
from tests.conftest import web3


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

    @staticmethod
    def patch_web3_block_data(web3, mocker, base_fee):
        # TODO: Build a new testchain with a node which provides EIP-1559 baseFee in getBlock response.
        block_data = dict(web3.eth.get_block('pending'))
        block_data['baseFeePerGas'] = base_fee
        mocker.patch.object(web3.eth, 'get_block', return_value=AttributeDict(block_data))

    def test_retrieve_node_gas_price(self, web3, mocker):
        strategy = TestNodeAwareGasPrice.DumbSampleImplementation(web3)
        assert strategy.get_gas_price(0) > 0
        assert strategy.get_gas_price(60) < strategy.get_gas_price(120)

        base_fee = 7 * GasStrategy.GWEI
        self.patch_web3_block_data(web3, mocker, base_fee)
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


class TestGeometricGasPrice:
    def test_gas_price_should_increase_with_time(self):
        # given
        geometric_gas_price = GeometricGasPrice(initial_price=100, initial_feecap=200, initial_tip=1, every_secs=10)

        # expect
        assert geometric_gas_price.get_gas_price(0) == 100
        assert geometric_gas_price.get_gas_price(1) == 100
        assert geometric_gas_price.get_gas_price(10) == 113
        assert geometric_gas_price.get_gas_price(15) == 113
        assert geometric_gas_price.get_gas_price(20) == 127
        assert geometric_gas_price.get_gas_price(30) == 143
        assert geometric_gas_price.get_gas_price(50) == 181
        assert geometric_gas_price.get_gas_price(100) == 325

        # TODO: test geometric_gas_price.get_gas_fees()

    def test_gas_price_should_obey_max_value(self):
        # given
        geometric_gas_price = GeometricGasPrice(initial_price=1000, initial_feecap=2000, initial_tip=10,
                                                every_secs=60, coefficient=1.125, max_price=2500)

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

        # TODO: test geometric_gas_price.get_gas_fees()

    def test_behaves_with_realistic_values(self):
        # given
        GWEI = 1000000000
        geometric_gas_price = GeometricGasPrice(initial_price=100*GWEI, initial_feecap=200*GWEI, initial_tip=1*GWEI,
                                                every_secs=10, coefficient=1+(0.125*2))

        for seconds in [0,1,10,12,30,60]:
            print(f"gas price after {seconds} seconds is {geometric_gas_price.get_gas_price(seconds)/GWEI}")

        assert round(geometric_gas_price.get_gas_price(0) / GWEI, 1) == 100.0
        assert round(geometric_gas_price.get_gas_price(1) / GWEI, 1) == 100.0
        assert round(geometric_gas_price.get_gas_price(10) / GWEI, 1) == 125.0
        assert round(geometric_gas_price.get_gas_price(12) / GWEI, 1) == 125.0
        assert round(geometric_gas_price.get_gas_price(30) / GWEI, 1) == 195.3
        assert round(geometric_gas_price.get_gas_price(60) / GWEI, 1) == 381.5

        # TODO: test geometric_gas_price.get_gas_fees()

    def test_should_require_positive_initial_price(self):
        with pytest.raises(AssertionError):
            GeometricGasPrice(0, None, None, 60)
        with pytest.raises(AssertionError):
            GeometricGasPrice(None, 0, 0, 60)

        with pytest.raises(AssertionError):
            GeometricGasPrice(-1, None, None, 60)
        with pytest.raises(AssertionError):
            GeometricGasPrice(None, -1, -1, 60)

    def test_should_require_positive_every_secs_value(self):
        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, None, None, 0)
        with pytest.raises(AssertionError):
            GeometricGasPrice(None, 600, 50, 0)

        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, None, None, -1)
        with pytest.raises(AssertionError):
            GeometricGasPrice(None, 600, 50, -1)

    def test_should_require_positive_coefficient(self):
        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 600, 50, 60, 0)

        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 600, 50, 60, 1)

        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 600, 50, 60, -1)

    def test_should_require_positive_max_price_if_provided(self):
        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 600, 50, 60, 1.125, 0)

        with pytest.raises(AssertionError):
            GeometricGasPrice(1000, 600, 50, 60, 1.125, -1)

    def test_max_price_should_exceed_initial_price(self):
        with pytest.raises(AssertionError):
            GeometricGasPrice(6000, 600, 50, 30, 2.25, 5000)

        with pytest.raises(AssertionError):
            GeometricGasPrice(None, 300, 5, 30, 1.424, 200)
