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

import argparse
import time

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.sai.Tub import Tub
from api.token.ERC20Token import ERC20Token
from api.feed.DSValue import DSValue
from keepers.Keeper import Keeper


class SaiTopUpCups(Keeper):
    def args(self, parser: argparse.ArgumentParser):
        parser.add_argument("--frequency", help="Monitoring frequency in seconds (default: 5)", default=5, type=float)
        parser.add_argument("--minimum-margin", help="Margin between the liquidation ratio and the top-up threshold (default: 0.1)", default=0.1, type=int)
        parser.add_argument("--target-margin", help="Margin between the liquidation ratio and the top-up target (default: 0.25)", default=0.25, type=float)

    def init(self):
        self.tub_address = Address(self.config.get_contract_address("saiTub"))
        self.tap_address = Address(self.config.get_contract_address("saiTap"))
        self.top_address = Address(self.config.get_contract_address("saiTop"))
        self.tub = Tub(web3=self.web3, address_tub=self.tub_address, address_tap=self.tap_address, address_top=self.top_address)
        self.tip = DSValue(web3=self.web3, address=self.tub.tip())
        self.skr = ERC20Token(web3=self.web3, address=self.tub.skr())

        self.liquidation_ratio = self.tub.mat()
        self.minimum_ratio = self.liquidation_ratio + Ray.from_number(self.arguments.minimum_margin)
        self.target_ratio = self.liquidation_ratio + Ray.from_number(self.arguments.target_margin)

    def run(self):
        while True:
            print(f"")
            for cup_id in range(1, self.tub.cupi()+1):
                cup = self.tub.cups(cup_id)
                if cup.lad == self.our_address:
                    pro = cup.ink*self.tub.tag()
                    tab = self.tub.tab(cup_id)
                    if tab == Wad(0):
                        print(f"Cup {cup_id} has no debt (SAI) drawn from it, definitely no need for top-up")
                        continue

                    current_ratio = Ray(pro / tab)

                    if current_ratio < self.minimum_ratio:
                        top_up_amount = tab * (Wad(self.target_ratio - current_ratio) / self.tub.tag())
                        print(f"Cup {cup_id} has collateralization ratio {current_ratio}, below {self.minimum_ratio}")
                        print(f"Cup {cup_id} needs top-up with {top_up_amount} SKR so the collateralization ratio reaches {self.target_ratio}")

                        skr_allowance = self.skr.allowance_of(self.our_address, self.tub.jar())
                        skr_balance = self.skr.balance_of(self.our_address)

                        if skr_balance < top_up_amount:
                            print(f"Cannot perform the top-up as our balance is only {skr_balance} SKR, less than {top_up_amount} SKR")
                        else:
                            if (skr_allowance < top_up_amount):
                                print(f"Current allowance is only {skr_allowance} SKR, which is less than {top_up_amount} SKR, raising it")
                                if not self.skr.approve(self.tub.jar(), Wad(2**256-1)):
                                    print("*** FAILED to raise allowance, the top-up will probably fail as well!")

                            if self.tub.lock(cup_id, top_up_amount):
                                print(f"Cup {cup_id} has been topped up with {top_up_amount} SKR")
                            else:
                                print(f"*** FAILED to top-up cup {cup_id}!")
                    else:
                        print(
                            f"Cup {cup_id} has collateralization ratio {current_ratio}, above {self.minimum_ratio}, no need for top-up")

            time.sleep(self.arguments.frequency)


if __name__ == '__main__':
    SaiTopUpCups().start()
