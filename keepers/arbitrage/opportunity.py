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
        self.conversions = conversions

    def total_rate(self) -> Ray:
        """Calculates the multiplication of all conversion rates forming this opportunity.

        A `total_rate` > 1.0 is a general indication that this opportunity may be profitable.
        """
        return reduce(operator.mul, map(lambda conversion: conversion.rate, self.conversions), Ray.from_number(1.0))

    def profit(self, currency: Address) -> Wad:
        """Calculates the expected profit brought by this opportunity (in token `token`)."""
        result = Wad.from_number(0)
        for conversion in self.conversions:
            if conversion.source_token == currency:
                result -= conversion.source_amount
            if conversion.target_token == currency:
                result += conversion.target_amount
        return result

    def tx_costs(self) -> Wad:
        """Calculates the transaction costs that this opportunity will take to execute."""
        #TODO lowered the transaction costs so the keeper is more aggressive, for testing purposes
        return Wad.from_number(0.0003) * len(self.conversions)

    def net_profit(self, token: Address) -> Wad:
        """Calculates the expected net profit brought by this opportunity (in token `token`).

        net_profit = profit - tx_costs
        """
        return self.profit(token) - self.tx_costs()

    def __str__(self):
        sai = Address('0x224c2202792b11c5ac5baaaa8284e6edb60f7174')
        return f"  Opportunity with profit={self.profit(sai)} SAI, tx_costs={self.tx_costs()} SAI, net_profit={self.net_profit(sai)} SAI" +\
               "".join(map(lambda conversion: "\n  " + str(conversion), self.conversions))
