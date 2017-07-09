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
    def __init__(self, conversions: List[Conversion]):
        assert(isinstance(conversions, list))
        self.steps = copy.deepcopy(conversions)
        self._validate_token_chain()

    def total_rate(self) -> Ray:
        """Calculates the multiplication of all conversion rates forming this sequence.

        A `total_rate` > 1.0 is a general indication that executing this sequence may be profitable.
        """
        return reduce(operator.mul, map(lambda step: step.rate, self.steps), Ray.from_number(1.0))

    def profit(self, token: Address) -> Wad:
        """Calculates the expected profit brought by executing this sequence (in token `token`)."""
        return sum(map(lambda s: s.target_amount, filter(lambda s: s.target_token == token, self.steps)), Wad(0)) \
               - sum(map(lambda s: s.source_amount, filter(lambda s: s.source_token == token, self.steps)), Wad(0))

    def tx_costs(self) -> Wad:
        """Calculates the transaction costs that this sequence will take to execute."""
        #TODO lowered the transaction costs so the keeper is more aggressive, for testing purposes
        return Wad.from_number(0.0003) * Wad.from_number(len(self.steps))

    def net_profit(self, token: Address) -> Wad:
        """Calculates the expected net profit brought by executing this sequence (in token `token`).

        net_profit = profit - tx_costs
        """
        return self.profit(token) - self.tx_costs()

    def set_amounts(self, initial_amount: Wad):
        def recalculate_previous_amounts(from_step_id: int):
            for id in range(from_step_id, -1, -1):
                self.steps[id].target_amount = self.steps[id + 1].source_amount
                self.steps[id].source_amount = Wad(Ray(self.steps[id].target_amount) / self.steps[id].rate)

        assert(isinstance(initial_amount, Wad))
        for i in range(len(self.steps)):
            if i == 0:
                self.steps[0].source_amount = initial_amount
            else:
                self.steps[i].source_amount = self.steps[i - 1].target_amount
            if self.steps[i].source_amount > self.steps[i].max_source_amount:
                self.steps[i].source_amount = self.steps[i].max_source_amount
                recalculate_previous_amounts(i - 1)
            self.steps[i].target_amount = Wad(Ray(self.steps[i].source_amount) * self.steps[i].rate)

    def _validate_token_chain(self):
        for i in range(1, len(self.steps)):
            assert(self.steps[i - 1].target_token == self.steps[i].source_token)


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

                sequence = Sequence(conversions=conversions)
                sequence.set_amounts(max_engagement)
                opportunities.append(sequence)

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
