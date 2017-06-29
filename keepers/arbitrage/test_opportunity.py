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

from api import Address
from api.numeric import Ray
from api.numeric import Wad
from keepers.arbitrage.conversion import Conversion
from keepers.arbitrage.opportunity import Opportunity, OpportunityFinder


class TestOpportunity:
    @pytest.fixture
    def token1(self):
        return Address('0x0101010101010101010101010101010101010101')

    @pytest.fixture
    def token2(self):
        return Address('0x0202020202020202020202020202020202020202')

    def test_should_calculate_total_rate(self, token1, token2):
        # given
        conversion1 = Conversion(token1, token2, Ray.from_number(1.01), Wad.from_number(1000), 'met1')
        conversion2 = Conversion(token2, token1, Ray.from_number(1.02), Wad.from_number(1000), 'met2')

        # when
        opportunity = Opportunity([conversion1, conversion2])

        # then
        assert opportunity.total_rate() == Ray.from_number(1.0302)

    def test_should_calculate_profit_and_net_profit(self, token1, token2):
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

    def test_should_calculate_tx_costs(self, token1, token2):
        # expect the tx_costs to be non negative and to increase with the number of conversions
        conversions = []
        prev_tx_costs = Wad.from_number(0)
        for i in range(10):
            conversions.append(Conversion(token1, token2, Ray(0), Wad(0), 'met'))
            opportunity = Opportunity(conversions)
            tx_costs = opportunity.tx_costs()
            assert(tx_costs > prev_tx_costs)
            prev_tx_costs = tx_costs


class TestOpportunityFinder:
    @pytest.fixture
    def token1(self):
        return Address('0x0101010101010101010101010101010101010101')

    @pytest.fixture
    def token2(self):
        return Address('0x0202020202020202020202020202020202020202')

    @pytest.fixture
    def token3(self):
        return Address('0x0303030303030303030303030303030303030303')

    @pytest.fixture
    def token4(self):
        return Address('0x0404040404040404040404040404040404040404')

    def test_should_identify_opportunity(self, token1, token2):
        # given
        conversion1 = Conversion(token1, token2, Ray.from_number(1.02), Wad.from_number(10000), 'met1')
        conversion2 = Conversion(token2, token1, Ray.from_number(1.03), Wad.from_number(10000), 'met2')
        conversions = [conversion1, conversion2]
        base_token = token1

        # when
        opportunities = OpportunityFinder(conversions).find_opportunities(base_token, Wad.from_number(100))

        # then
        assert len(opportunities) == 1
        assert len(opportunities[0].conversions) == 2
        assert opportunities[0].conversions[0].method == "met1"
        assert opportunities[0].conversions[1].method == "met2"

    def test_opportunities_found_should_start_with_the_base_token(self, token1, token2):
        # given
        conversion1 = Conversion(token1, token2, Ray.from_number(1.02), Wad.from_number(10000), 'met1')
        conversion2 = Conversion(token2, token1, Ray.from_number(1.03), Wad.from_number(10000), 'met2')
        conversions = [conversion1, conversion2]
        base_token = token2

        # when
        opportunities = OpportunityFinder(conversions).find_opportunities(base_token, Wad.from_number(100))

        # then
        assert len(opportunities) == 1
        assert len(opportunities[0].conversions) == 2
        assert opportunities[0].conversions[0].method == "met2"
        assert opportunities[0].conversions[1].method == "met1"

    def test_should_identify_multi_step_opportunities(self, token1, token2, token3, token4):
        # given
        conversion1 = Conversion(token1, token2, Ray.from_number(1.02), Wad.from_number(10000), 'met1')
        conversion2 = Conversion(token2, token3, Ray.from_number(1.03), Wad.from_number(10000), 'met2')
        conversion3 = Conversion(token3, token4, Ray.from_number(1.05), Wad.from_number(10000), 'met3')
        conversion4 = Conversion(token4, token1, Ray.from_number(1.07), Wad.from_number(10000), 'met4')
        conversions = [conversion1, conversion2, conversion3, conversion4]
        base_token = token1

        # when
        opportunities = OpportunityFinder(conversions).find_opportunities(base_token, Wad.from_number(100))

        # then
        assert len(opportunities) == 1
        assert len(opportunities[0].conversions) == 4
        assert opportunities[0].conversions[0].method == "met1"
        assert opportunities[0].conversions[1].method == "met2"
        assert opportunities[0].conversions[2].method == "met3"
        assert opportunities[0].conversions[3].method == "met4"

    def test_should_ignore_irrelevant_conversions(self, token1, token2, token3, token4):
        # given
        conversion1 = Conversion(token1, token2, Ray.from_number(1.02), Wad.from_number(10000), 'met1')
        conversion2 = Conversion(token2, token1, Ray.from_number(1.03), Wad.from_number(10000), 'met2')
        conversion3 = Conversion(token1, token3, Ray.from_number(1.04), Wad.from_number(10000), 'met3')
        conversion4 = Conversion(token1, token4, Ray.from_number(1.07), Wad.from_number(10000), 'met4')
        conversion5 = Conversion(token2, token4, Ray.from_number(1.08), Wad.from_number(10000), 'met5')
        conversions = [conversion1, conversion2, conversion3, conversion4, conversion5]
        base_token = token1

        # when
        opportunities = OpportunityFinder(conversions).find_opportunities(base_token, Wad.from_number(100))

        # then
        assert len(opportunities) == 1
        assert len(opportunities[0].conversions) == 2
        assert opportunities[0].conversions[0].method == "met1"
        assert opportunities[0].conversions[1].method == "met2"

    def test_should_identify_all_opportunities_regardless_whether_they_are_profitable(self, token1, token2):
        # given
        conversion1 = Conversion(token1, token2, Ray.from_number(1.1), Wad.from_number(10000), 'met1')
        conversion2 = Conversion(token2, token1, Ray.from_number(0.6), Wad.from_number(10000), 'met2')
        conversions = [conversion1, conversion2]
        base_token = token1

        # when
        opportunities = OpportunityFinder(conversions).find_opportunities(base_token, Wad.from_number(100))

        # then
        assert len(opportunities) == 1
        assert len(opportunities[0].conversions) == 2
        assert opportunities[0].conversions[0].method == "met1"
        assert opportunities[0].conversions[1].method == "met2"

    def test_should_recognize_if_there_are_no_opportunities(self, token1, token2, token3):
        # given
        conversion1 = Conversion(token1, token2, Ray.from_number(1.02), Wad.from_number(10000), 'met1')
        conversion2 = Conversion(token2, token3, Ray.from_number(1.03), Wad.from_number(10000), 'met2')
        conversions = [conversion1, conversion2]
        base_token = token1

        # when
        opportunities = OpportunityFinder(conversions).find_opportunities(base_token, Wad.from_number(100))

        # then
        assert len(opportunities) == 0

    def test_should_calculate_amounts_based_on_rates(self, token1, token2, token3, token4):
        # given
        conversion1 = Conversion(token1, token2, Ray.from_number(2.0), Wad.from_number(10000), 'met1')
        conversion2 = Conversion(token2, token3, Ray.from_number(1.6), Wad.from_number(10000), 'met2')
        conversion3 = Conversion(token3, token4, Ray.from_number(1.2), Wad.from_number(10000), 'met3')
        conversion4 = Conversion(token4, token1, Ray.from_number(1.1), Wad.from_number(10000), 'met4')
        conversions = [conversion1, conversion2, conversion3, conversion4]
        base_token = token1

        # when
        opportunities = OpportunityFinder(conversions).find_opportunities(base_token, Wad.from_number(100))

        # then
        assert len(opportunities) == 1
        assert len(opportunities[0].conversions) == 4
        assert opportunities[0].conversions[0].method == "met1"
        assert opportunities[0].conversions[0].source_amount == Wad.from_number(100)
        assert opportunities[0].conversions[0].target_amount == Wad.from_number(200)
        assert opportunities[0].conversions[1].method == "met2"
        assert opportunities[0].conversions[1].source_amount == Wad.from_number(200)
        assert opportunities[0].conversions[1].target_amount == Wad.from_number(320)
        assert opportunities[0].conversions[2].method == "met3"
        assert opportunities[0].conversions[2].source_amount == Wad.from_number(320)
        assert opportunities[0].conversions[2].target_amount == Wad.from_number(384)
        assert opportunities[0].conversions[3].method == "met4"
        assert opportunities[0].conversions[3].source_amount == Wad.from_number(384)
        assert opportunities[0].conversions[3].target_amount == Wad.from_number(422.4)

    def test_should_adjust_amounts_based_on_max_source_amount(self, token1, token2, token3, token4):
        # given
        conversion1 = Conversion(token1, token2, Ray.from_number(2.0), Wad.from_number(10000), 'met1')
        conversion2 = Conversion(token2, token3, Ray.from_number(1.6), Wad.from_number(10000), 'met2')
        conversion3 = Conversion(token3, token4, Ray.from_number(1.2), Wad.from_number(100), 'met3')
        conversion4 = Conversion(token4, token1, Ray.from_number(1.1), Wad.from_number(10000), 'met4')
        conversions = [conversion1, conversion4, conversion3, conversion2]
        base_token = token1

        # when
        opportunities = OpportunityFinder(conversions).find_opportunities(base_token, Wad.from_number(100))

        # then
        assert len(opportunities) == 1
        assert len(opportunities[0].conversions) == 4
        assert opportunities[0].conversions[0].method == "met1"
        assert opportunities[0].conversions[0].source_amount == Wad.from_number(31.25)
        assert opportunities[0].conversions[0].target_amount == Wad.from_number(62.5)
        assert opportunities[0].conversions[1].method == "met2"
        assert opportunities[0].conversions[1].source_amount == Wad.from_number(62.5)
        assert opportunities[0].conversions[1].target_amount == Wad.from_number(100)
        assert opportunities[0].conversions[2].method == "met3"
        assert opportunities[0].conversions[2].source_amount == Wad.from_number(100)
        assert opportunities[0].conversions[2].target_amount == Wad.from_number(120)
        assert opportunities[0].conversions[3].method == "met4"
        assert opportunities[0].conversions[3].source_amount == Wad.from_number(120)
        assert opportunities[0].conversions[3].target_amount == Wad.from_number(132)
