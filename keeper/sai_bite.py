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
import sys

from keeper.sai import SaiKeeper


class SaiBite(SaiKeeper):
    """SAI keeper to bite undercollateralized cups.

    Keeper constantly looks for unsafe cups and bites them the moment they become
    unsafe. Ultimately, it should take into account the profit it can make by processing
    the resulting collateral via `bust` and only waste gas on `bite` if it can make it up
    by subsequent arbitrage. For now, it is a dumb keeper that just bites every cup
    that can be bitten.
    """

    def startup(self):
        self.on_block(self.check_all_cups)

    def check_all_cups(self):
        for cup_id in range(self.tub.cupi()):
            self.check_cup(cup_id+1)

    def check_cup(self, cup_id):
        if not self.tub.safe(cup_id):
            self.tub.bite(cup_id).transact(gas_price=self.gas_price)


if __name__ == '__main__':
    SaiBite(sys.argv[1:]).start()
