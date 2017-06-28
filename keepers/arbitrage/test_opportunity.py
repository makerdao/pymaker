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

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from keepers.arbitrage.conversion import Conversion
from keepers.arbitrage.opportunity import Opportunity


@pytest.fixture
def token1():
    return Address('0x0101010101010101010101010101010101010101')


@pytest.fixture
def token2():
    return Address('0x0202020202020202020202020202020202020202')


def test_should_calculate_total_rate(token1, token2):
    # given
    conversion1 = Conversion(token1, token2, Ray.from_number(1.01), Wad.from_number(1000), 'met1')
    conversion2 = Conversion(token2, token1, Ray.from_number(1.02), Wad.from_number(1000), 'met2')
    
    # when
    opportunity = Opportunity([conversion1, conversion2])

    # then
    assert opportunity.total_rate() == Ray.from_number(1.0302)


def test_should_calculate_profit_and_net_profit(token1, token2):
    # given
    conversion1 = Conversion(token1, token2, Ray.from_number(1.01), Wad.from_number(1000), 'met1')
    conversion1.source_amount = Wad.from_number(100)
    conversion1.target_amount = Wad.from_number(101)
    conversion2 = Conversion(token2, token1, Ray.from_number(1.02), Wad.from_number(1000), 'met2')
    conversion2.source_amount = Wad.from_number(101)
    conversion2.target_amount = Wad.from_number(103.02)
    
    # when
    opportunity = Opportunity([conversion1, conversion2])

    # then
    assert opportunity.profit(token1) == Wad.from_number(3.02)
    assert opportunity.profit(token2) == Wad.from_number(0)
    assert opportunity.net_profit(token1) == opportunity.profit(token1) - opportunity.tx_costs()
    assert opportunity.net_profit(token2) == opportunity.profit(token2) - opportunity.tx_costs()


def test_should_calculate_tx_costs(token1, token2):
    # expect the tx_costs to be non negative and to increase with the number of conversions
    conversions = []
    prev_tx_costs = Wad.from_number(0)
    for i in range(10):
        conversions.append(Conversion(token1, token2, Ray(0), Wad(0), 'met'))
        opportunity = Opportunity(conversions)
        tx_costs = opportunity.tx_costs()
        assert(tx_costs > prev_tx_costs)
        prev_tx_costs = tx_costs
