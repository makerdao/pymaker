#!/usr/bin/env python3
#
# This file is part of "maker.py".
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
import copy
from pprint import pformat
from typing import List

from api.Ray import Ray
from api.Wad import Wad
from keepers.arbitrage.Conversion import Conversion


class Opportunity:
    def __init__(self, conversions: List[Conversion]):
        assert(isinstance(conversions, list))
        self.conversions = copy.deepcopy(conversions)

    def total_rate(self) -> Ray:
        output = Ray.from_number(1.0)
        for conversion in self.conversions:
            output = output * conversion.rate
        return output

    def discover_prices(self, our_max_engagement: Wad):
        def backcalculate_amounts(from_conversion_id: int):
            for id in range(from_conversion_id, -1, -1):
                self.conversions[id].to_amount = self.conversions[id+1].from_amount
                self.conversions[id].from_amount = Wad(Ray(self.conversions[id].to_amount) / self.conversions[id].rate)

        assert(isinstance(our_max_engagement, Wad))
        self.conversions[0].from_amount = Wad.min(our_max_engagement, self.conversions[0].max_from_amount)
        self.conversions[0].to_amount = self.conversions[0].from_amount * self.conversions[0].rate

        for i in range(1, len(self.conversions)):
            assert(self.conversions[i-1].to_currency == self.conversions[i].from_currency)
            self.conversions[i].from_amount = self.conversions[i-1].to_amount
            if self.conversions[i].from_amount > self.conversions[i].max_from_amount:
                self.conversions[i].from_amount = self.conversions[i].max_from_amount
                backcalculate_amounts(i-1)
            self.conversions[i].to_amount = Wad(Ray(self.conversions[i].from_amount) * self.conversions[i].rate)

    def profit(self, currency: str):
        profit = Wad.from_number(0)
        for conversion in self.conversions:
            if conversion.from_currency == currency:
                profit -= conversion.from_amount
            if conversion.to_currency == currency:
                profit += conversion.to_amount
        return profit

    def tx_profit(self):
        return self.profit('SAI')

    def tx_costs(self):
        return Wad.from_number(0.3) * len(self.conversions)

    def tx_total_profit(self):
        return self.tx_profit()-self.tx_costs()

    def __str__(self):
        return f"  Opportunity with tx_profit={self.tx_profit()} SAI, tx_costs={self.tx_costs()} SAI, tx_total_profit={self.tx_total_profit()}" + "".join(map(lambda conversion: "\n  " + repr(conversion), self.conversions))
