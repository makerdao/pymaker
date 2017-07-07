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

import logging

from api import Address
from api.token import ERC20Token
from api.numeric import Ray
from api.numeric import Wad
from api.sai import Tub
from keepers import Keeper


class SaiTopUp(Keeper):
    def args(self, parser: argparse.ArgumentParser):
        parser.add_argument("--frequency", help="Monitoring frequency in seconds (default: 5)", default=5, type=int)
        parser.add_argument("--minimum-margin", help="Margin between the liquidation ratio and the top-up threshold (default: 0.1)", default=0.1, type=float)
        parser.add_argument("--target-margin", help="Margin between the liquidation ratio and the top-up target (default: 0.25)", default=0.25, type=float)

    def init(self):
        self.tub_address = Address(self.config.get_contract_address("saiTub"))
        self.tap_address = Address(self.config.get_contract_address("saiTap"))
        self.top_address = Address(self.config.get_contract_address("saiTop"))
        self.tub = Tub(web3=self.web3, address_tub=self.tub_address, address_tap=self.tap_address, address_top=self.top_address)
        self.skr = ERC20Token(web3=self.web3, address=self.tub.skr())

        self.liquidation_ratio = self.tub.mat()
        self.minimum_ratio = self.liquidation_ratio + Ray.from_number(self.arguments.minimum_margin)
        self.target_ratio = self.liquidation_ratio + Ray.from_number(self.arguments.target_margin)

    def run(self):
        self.setup_allowance(self.tub.jar(), 'Tub.jar')
        while True:
            self.check_all_cups()
            time.sleep(self.arguments.frequency)

    def setup_allowance(self, spender_address: Address, spender_name: str):
        if self.skr.allowance_of(self.our_address, spender_address) < Wad(2 ** 128 - 1):
            logging.info(f"Approving {spender_name} ({spender_address}) to access our SKR balance...")
            logging.info(f"")
            self.skr.approve(spender_address)

    def check_all_cups(self):
        for cup in self.our_cups():
            self.check_cup(cup)

    def check_cup(self, cup):
        top_up_amount = self.required_top_up(cup)
        if top_up_amount:
            if top_up_amount >= self.skr.balance_of(self.our_address):
                self.tub.lock(cup.cup_id, top_up_amount)
            else:
                logging.info(f"Cannot top-up as our balance is less than {top_up_amount} SKR.")

    def our_cups(self):
        for cup_id in range(1, self.tub.cupi()+1):
            cup = self.tub.cups(cup_id)
            if cup.lad == self.our_address:
                yield cup

    def required_top_up(self, cup):
        pro = cup.ink*self.tub.tag()
        tab = self.tub.tab(cup.cup_id)
        if tab > Wad(0):
            current_ratio = Ray(pro / tab)
            if current_ratio < self.minimum_ratio:
                return tab * (Wad(self.target_ratio - current_ratio) / self.tub.tag())
            else:
                return None
        else:
            return None


if __name__ == '__main__':
    SaiTopUp().start()
