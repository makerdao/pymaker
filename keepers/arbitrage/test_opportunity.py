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

from api.Ray import Ray
from api.Wad import Wad
from keepers.arbitrage.Conversion import Conversion
from keepers.arbitrage.Opportunity import Opportunity


def test_should_calculate_total_rate():
    # given
    conversion1 = Conversion('ABC', 'DEF', Ray.from_number(1.01), Wad.from_number(1), Wad.from_number(100), 'met')
    conversion2 = Conversion('DEF', 'ABC', Ray.from_number(1.02), Wad.from_number(1), Wad.from_number(100), 'met')
    opportunity = Opportunity([conversion1, conversion2])

    # except
    assert opportunity.total_rate() == Ray.from_number(1.0302)
