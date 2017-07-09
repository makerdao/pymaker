#!/usr/bin/env python3
#
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

from keepers.sai import SaiKeeper


class SaiBite(SaiKeeper):
    def startup(self):
        self.on_block(self.check_all_cups)

    def check_all_cups(self):
        for cup_id in range(self.tub.cupi()):
            self.check_cup(cup_id+1)

    def check_cup(self, cup_id):
        if not self.tub.safe(cup_id):
            self.tub.bite(cup_id)


if __name__ == '__main__':
    SaiBite().start()
