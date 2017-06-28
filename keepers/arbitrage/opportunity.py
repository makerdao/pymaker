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

import copy
import operator
from functools import reduce
from typing import List

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from keepers.arbitrage.conversion import Conversion


class Opportunity:
    def __init__(self, conversions: List[Conversion]):
        assert(isinstance(conversions, list))
        self.conversions = copy.deepcopy(conversions)

    def discover_prices(self, our_max_engagement: Wad):
        def backcalculate_amounts(from_conversion_id: int):
            for id in range(from_conversion_id, -1, -1):
                self.conversions[id].to_amount = self.conversions[id+1].from_amount
                self.conversions[id].from_amount = Wad(Ray(self.conversions[id].to_amount) / self.conversions[id].rate)

        assert(isinstance(our_max_engagement, Wad))
        self.conversions[0].from_amount = Wad.min(our_max_engagement, self.conversions[0].max_from_amount)
        self.conversions[0].to_amount = self.conversions[0].from_amount * self.conversions[0].rate

        for i in range(1, len(self.conversions)):
            assert(self.conversions[i-1].target_token == self.conversions[i].source_token)
            self.conversions[i].from_amount = self.conversions[i-1].to_amount
            if self.conversions[i].from_amount > self.conversions[i].max_from_amount:
                self.conversions[i].from_amount = self.conversions[i].max_from_amount
                backcalculate_amounts(i-1)
            self.conversions[i].to_amount = Wad(Ray(self.conversions[i].from_amount) * self.conversions[i].rate)

    def total_rate(self) -> Ray:
        return reduce(operator.mul, map(lambda conversion: conversion.rate, self.conversions), Ray.from_number(1.0))

    def profit(self, currency: Address) -> Wad:
        result = Wad.from_number(0)
        for conversion in self.conversions:
            if conversion.source_token == currency:
                result -= conversion.from_amount
            if conversion.target_token == currency:
                result += conversion.to_amount
        return result

    def tx_costs(self) -> Wad:
        #TODO lowered the transaction costs so the keeper is more aggressive, for testing purposes
        return Wad.from_number(0.0003) * len(self.conversions)

    def net_profit(self, currency: Address) -> Wad:
        return self.profit(currency) - self.tx_costs()

    def __str__(self):
        sai = Address('0x224c2202792b11c5ac5baaaa8284e6edb60f7174')
        return f"  Opportunity with profit={self.profit(sai)} SAI, tx_costs={self.tx_costs()} SAI, net_profit={self.net_profit(sai)} SAI" +\
               "".join(map(lambda conversion: "\n  " + str(conversion), self.conversions))
