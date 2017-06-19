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

import networkx as nx

from keepers.arbitrage.Opportunity import Opportunity


class OpportunityFinder:
    def __init__(self, conversions):
        assert(isinstance(conversions, list))
        self.conversions = conversions

    def opportunities(self, base_currency = 'SAI'):
        dod = {}
        for conversion in self.conversions:
            # for each currency XXX we create an XXX-last node with linked to XXX
            # this is in order to simplify simple paths finding
            if (conversion.from_currency + "-pre") not in dod:
                dod[conversion.from_currency + "-pre"] = {conversion.from_currency: {'weight': 1}}

            # now we create a link between our currency pairs
            if conversion.from_currency not in dod:
                dod[conversion.from_currency] = {}

            dod[conversion.from_currency][conversion.to_currency + "-pre"] = {'weight': 1, 'conversion': conversion}

        G=nx.DiGraph(dod)
        paths = list(nx.shortest_simple_paths(G, base_currency, base_currency + "-pre"))
        print(paths)

        opportunities = []
        for path in paths:
            conversions = []
            for i in range(0, len(path)-1):
                if 'conversion' in dod[path[i]][path[i+1]]:
                    conversions.append(dod[path[i]][path[i+1]]['conversion'])
            opportunities.append(Opportunity(conversions=conversions))

        return opportunities
