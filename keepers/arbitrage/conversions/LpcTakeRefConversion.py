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
from api.sai.Lpc import Lpc
from api.token.ERC20Token import ERC20Token
from keepers.arbitrage.Conversion import Conversion


class LpcTakeRefConversion(Conversion):
    def __init__(self, lpc: Lpc):
        self.lpc = lpc
        rate = Ray(self.lpc.tag() / (self.lpc.par() * self.lpc.gap()))
        #TODO we always leave 0.000001 in the liquidity pool, in case of some rounding errors
        max_entry_alt = Wad.max((ERC20Token(web3=lpc.web3, address=lpc.ref()).balance_of(lpc.address) / Wad(rate)) - Wad.from_number(0.000001), Wad.from_number(0))
        super().__init__(source_token=self.lpc.alt(),
                         target_token=self.lpc.ref(),
                         rate=rate,
                         min_from_amount=Wad.from_number(0),
                         max_from_amount=max_entry_alt,
                         method="lpc-take-ref")

    def execute(self):
        print(f"  Executing take(ref, '{self.to_amount}') on Lpc in order to exchange {self.from_amount} {self.lpc.alt()} to {self.to_amount} {self.lpc.ref()}")
        take_result = self.lpc.take(self.lpc.ref(), self.to_amount)
        if take_result:
            our_address = Address(self.lpc.web3.eth.defaultAccount)
            alt_transfer_on_take = next(filter(lambda transfer: transfer.token_address == self.lpc.alt() and transfer.from_address == our_address, take_result.transfers))
            ref_transfer_on_take = next(filter(lambda transfer: transfer.token_address == self.lpc.ref() and transfer.to_address == our_address, take_result.transfers))
            print(f"  Take was successful, exchanged {alt_transfer_on_take.value} {self.lpc.alt()} to {ref_transfer_on_take.value} {self.lpc.ref()}")
            return take_result
        else:
            print(f"  Take failed!")
            return None
