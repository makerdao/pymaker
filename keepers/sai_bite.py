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

import time

from api.Address import Address
from api.sai.Tub import Tub
from keepers import Keeper


class SaiBite(Keeper):
    def args(self, parser):
        parser.add_argument("--frequency", help="Monitoring frequency in seconds (default: 5)", default=5, type=int)

    def init(self):
        self.tub_address = Address(self.config.get_contract_address("saiTub"))
        self.tap_address = Address(self.config.get_contract_address("saiTap"))
        self.top_address = Address(self.config.get_contract_address("saiTop"))
        self.tub = Tub(web3=self.web3, address_tub=self.tub_address, address_tap=self.tap_address, address_top=self.top_address)

    def run(self):
        while True:
            self.check_all_cups()
            time.sleep(self.arguments.frequency)

    def check_all_cups(self):
        for cup_id in range(self.tub.cupi()):
            self.check_cup(cup_id+1)

    def check_cup(self, cup_id):
        if not self.tub.safe(cup_id):
            if self.tub.bite(cup_id):
                print(f"Cup {cup_id} has been bitten")
            else:
                print(f"Failed to bite cup {cup_id}")


if __name__ == '__main__':
    SaiBite().start()
