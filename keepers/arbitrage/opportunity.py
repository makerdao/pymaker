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

import networkx

from api import Address
from api.numeric import Ray
from api.numeric import Wad
from keepers.arbitrage.conversion import Conversion


class Sequence:
    def __init__(self, steps: List[Conversion]):
        assert(isinstance(steps, list))
        self.steps = steps

    def total_rate(self) -> Ray:
        """Calculates the multiplication of all conversion rates forming this sequence.

        A `total_rate` > 1.0 is a general indication that executing this sequence may be profitable.
        """
        return reduce(operator.mul, map(lambda conversion: conversion.rate, self.steps), Ray.from_number(1.0))

    def profit(self, currency: Address) -> Wad:
        """Calculates the expected profit brought by executing this sequence (in token `token`)."""
        result = Wad.from_number(0)
        for conversion in self.steps:
            if conversion.source_token == currency:
                result -= conversion.source_amount
            if conversion.target_token == currency:
                result += conversion.target_amount
        return result

    def tx_costs(self) -> Wad:
        """Calculates the transaction costs that this sequence will take to execute."""
        #TODO lowered the transaction costs so the keeper is more aggressive, for testing purposes
        return Wad.from_number(0.0003) * Wad.from_number(len(self.steps))

    def net_profit(self, token: Address) -> Wad:
        """Calculates the expected net profit brought by executing this sequence (in token `token`).

        net_profit = profit - tx_costs
        """
        return self.profit(token) - self.tx_costs()


class OpportunityFinder:
    def __init__(self, conversions):
        assert(isinstance(conversions, list))
        self.conversions = conversions

    def find_opportunities(self, base_token: Address, max_engagement: Wad):
        graph_links = self._prepare_graph_links()
        graph = networkx.DiGraph(graph_links)
        try:
            paths = list(networkx.shortest_simple_paths(graph, base_token.address, base_token.address + "-pre"))

            opportunities = []
            for path in paths:
                conversions = []
                for i in range(0, len(path)-1):
                    if 'conversion' in graph_links[path[i]][path[i+1]]:
                        conversions.append(graph_links[path[i]][path[i+1]]['conversion'])

                chain_of_conversions = copy.deepcopy(conversions)
                self._validate_token_chain(chain_of_conversions)
                self._discover_prices(chain_of_conversions, max_engagement)
                opportunities.append(Sequence(steps=chain_of_conversions))

            return opportunities
        except networkx.exception.NetworkXNoPath:
            return []

    def _prepare_graph_links(self):
        def add_empty_link(dod, link_from, link_to):
            if link_from not in dod:
                dod[link_from] = {}
            dod[link_from][link_to] = {}

        def add_conversion_link(dod, link_from, link_to, conversion):
            if link_from not in dod:
                dod[link_from] = {}
            dod[link_from][link_to] = {'conversion': conversion}

        links = {}
        for conversion in self.conversions:
            src = conversion.source_token.address
            dst = conversion.target_token.address
            add_empty_link(links, src + "-pre", src)
            add_conversion_link(links, src, dst + "-via-" + conversion.method, conversion)
            add_empty_link(links, dst + "-via-" + conversion.method, dst + "-pre")
        return links

    def _backcalculate_amounts(self, chain_of_conversions: list, from_conversion_id: int):
        for id in range(from_conversion_id, -1, -1):
            chain_of_conversions[id].target_amount = chain_of_conversions[id + 1].source_amount
            chain_of_conversions[id].source_amount = Wad(Ray(chain_of_conversions[id].target_amount) / chain_of_conversions[id].rate)

    def _validate_token_chain(self, chain_of_conversions: list):
        for i in range(1, len(chain_of_conversions)):
            assert(chain_of_conversions[i - 1].target_token == chain_of_conversions[i].source_token)

    def _discover_prices(self, chain_of_conversions: list, max_engagement: Wad):
        assert(isinstance(chain_of_conversions, list))
        assert(isinstance(max_engagement, Wad))
        for i in range(len(chain_of_conversions)):
            if i == 0:
                chain_of_conversions[0].source_amount = max_engagement
            else:
                chain_of_conversions[i].source_amount = chain_of_conversions[i - 1].target_amount
            if chain_of_conversions[i].source_amount > chain_of_conversions[i].max_source_amount:
                chain_of_conversions[i].source_amount = chain_of_conversions[i].max_source_amount
                self._backcalculate_amounts(chain_of_conversions, i - 1)
            chain_of_conversions[i].target_amount = Wad(Ray(chain_of_conversions[i].source_amount) * chain_of_conversions[i].rate)
