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

import networkx

from api.Wad import Wad
from keepers.arbitrage.Opportunity import Opportunity


class OpportunityFinder:
    def __init__(self, conversions):
        assert(isinstance(conversions, list))
        self.conversions = conversions

    def find_opportunities(self, base_currency: str, our_max_engagement: Wad):
        def empty_link(dod, link_from, link_to):
            if link_from not in dod:
                dod[link_from] = {}
            dod[link_from][link_to] = {}

        def conversion_link(dod, link_from, link_to, conversion):
            if link_from not in dod:
                dod[link_from] = {}
            dod[link_from][link_to] = {'conversion': conversion}

        def graph_links():
            dod = {}
            for conversion in self.conversions:
                empty_link(dod, conversion.from_currency + "-pre", conversion.from_currency)
                conversion_link(dod, conversion.from_currency, conversion.to_currency + "-via-" + conversion.method, conversion)
                empty_link(dod, conversion.to_currency + "-via-" + conversion.method, conversion.to_currency + "-pre")
            return dod

        graph_links = graph_links()
        graph = networkx.DiGraph(graph_links)
        try:
            paths = list(networkx.shortest_simple_paths(graph, base_currency, base_currency + "-pre"))

            opportunities = []
            for path in paths:
                conversions = []
                for i in range(0, len(path)-1):
                    if 'conversion' in graph_links[path[i]][path[i+1]]:
                        conversions.append(graph_links[path[i]][path[i+1]]['conversion'])

                opportunity = Opportunity(conversions=conversions)
                opportunity.discover_prices(our_max_engagement)
                opportunities.append(opportunity)

            return opportunities
        except networkx.exception.NetworkXNoPath:
            return []
