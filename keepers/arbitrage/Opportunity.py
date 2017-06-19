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

from pprint import pformat

from api.Ray import Ray


class Opportunity:
    def __init__(self, conversions):
        self.conversions = conversions

    def total_rate(self):
        output = Ray.from_number(1.0)
        for conversion in self.conversions:
            output = output * conversion.rate
        return output

    def __str__(self):
        return pformat(vars(self))

    def __repr__(self):
        return f"Opportunity via <{str(self.conversions)}> with total_rate={self.total_rate()}"
