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
import sys

from keeper.api.approval import directly
from keeper.api.numeric import Ray
from keeper.api.numeric import Wad
from keeper.sai import SaiKeeper


class SaiTopUp(SaiKeeper):
    """SAI keeper to top-up cups before they reach the liquidation ratio.

    Kepper constantly monitors cups owned by the `--eth-from` account. If the
    collateralization ratio falls under `mat` + `--min-margin`, the cup will get
    topped-up up to `mat` + `--top-up-margin`.

    TODO this keeper will evolve into a CDP management keeper.

    Cups owned by other accounts are ignored.
    """
    def __init__(self, args: list, **kwargs):
        super().__init__(args, **kwargs)
        self.liquidation_ratio = self.tub.mat()
        self.minimum_ratio = self.liquidation_ratio + Ray.from_number(self.arguments.min_margin)
        self.target_ratio = self.liquidation_ratio + Ray.from_number(self.arguments.top_up_margin)
        self.max_sai = Wad.from_number(self.arguments.max_sai)
        self.avg_sai = Wad.from_number(self.arguments.avg_sai)

    def args(self, parser: argparse.ArgumentParser):
        parser.add_argument("--min-margin", help="Margin between the liquidation ratio and the top-up threshold", type=float, required=True)
        parser.add_argument("--top-up-margin", help="Margin between the liquidation ratio and the top-up target", type=float, required=True)
        parser.add_argument("--max-sai", type=float, required=True)
        parser.add_argument("--avg-sai", type=float, required=True)

    def startup(self):
        self.approve()
        self.on_block(self.check_all_cups)

    def approve(self):
        self.tub.approve(directly())

    def check_all_cups(self):
        for cup in self.our_cups():
            self.check_cup(cup.cup_id)

    def check_cup(self, cup_id: int):
        assert(isinstance(cup_id, int))

        # If cup is undercollateralized and the amount of SAI we are holding is more than `--max-sai`
        # then we wipe some debt first so our balance reaches `--avg-sai`. Bear in mind that it is
        # possible that we pay all out debt this way and our SAI balance will still be higher
        # than `--max-sai`.
        if self.is_undercollateralized(cup_id) and self.sai.balance_of(self.our_address) > self.max_sai:
            amount_of_sai_to_wipe = self.calculate_sai_wipe()
            if amount_of_sai_to_wipe > Wad(0):
                self.tub.wipe(cup_id, amount_of_sai_to_wipe).transact(gas_price=self.gas_price)

        # If cup is still undercollateralized, calculate the amount of SKR needed to top it up so
        # the collateralization level reaches `--top-up-margin`. If we have enough ETH, exchange
        # in to SKR and then top-up the cup.
        if self.is_undercollateralized(cup_id):
            top_up_amount = self.calculate_skr_top_up(cup_id)
            if top_up_amount <= self.eth_balance(self.our_address):
                # TODO we do not always join with the same amount as the one we lock!
                self.tub.join(top_up_amount).transact(gas_price=self.gas_price)
                self.tub.lock(cup_id, top_up_amount).transact(gas_price=self.gas_price)
            else:
                self.logger.info(f"Cannot top-up as our balance is less than {top_up_amount} ETH.")

    def our_cups(self):
        for cup_id in range(1, self.tub.cupi()+1):
            cup = self.tub.cups(cup_id)
            if cup.lad == self.our_address:
                yield cup

    def is_undercollateralized(self, cup_id) -> bool:
        pro = self.tub.ink(cup_id)*self.tub.tag()
        tab = self.tub.tab(cup_id)
        if tab > Wad(0):
            current_ratio = Ray(pro / tab)
            print(current_ratio)
            print(self.minimum_ratio)
            return current_ratio < self.minimum_ratio
        else:
            return False

    def calculate_sai_wipe(self) -> Wad:
        """Calculates the amount of SAI that can be wiped.

        Calculates the amount of SAI than can be wiped in order to bring the SAI holdings
        to `--avg-sai`.
        """
        return Wad.max(self.sai.balance_of(self.our_address) - self.avg_sai, Wad(0))

    def calculate_skr_top_up(self, cup_id) -> Wad:
        """Calculates the required top-up in SKR.

        Calculates the required top-up in SKR in order to bring the collateralization level
        of the cup to `--target-ratio`.
        """
        pro = self.tub.ink(cup_id)*self.tub.tag()
        tab = self.tub.tab(cup_id)
        if tab > Wad(0):
            current_ratio = Ray(pro / tab)
            return Wad.max(tab * (Wad(self.target_ratio - current_ratio) / self.tub.tag()), Wad(0))
        else:
            return Wad(0)


if __name__ == '__main__':
    SaiTopUp(sys.argv[1:]).start()
