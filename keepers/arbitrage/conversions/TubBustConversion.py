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

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.sai import Tub
from keepers.arbitrage.conversion import Conversion


class TubBustConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(source_token=self.tub.sai(),
                         target_token=self.tub.skr(),
                         rate=(Ray.from_number(1) / Ray(tub.tap_ask())),
                         min_source_amount=Wad.from_number(0),
                         max_source_amount=self.bustable_amount_in_sai(tub),
                         method="tub-bust")

    def bustable_amount_in_sai(self, tub: Tub):
        #TODO we always try to bust 10 SAI less than what the Tub reports
        #in order to discount the growth of `joy()` that might've have happened since the last drip
        #of course this is not the right solution and it won't even work properly if the last
        #drip happened enough time ago
        return Wad.max(tub.woe() - tub.joy() - Wad.from_number(10), Wad.from_number(0))

    def name(self):
        return f"tub.bust('{self.target_amount}')"

    def execute(self):
        return self.tub.bust(self.target_amount)
