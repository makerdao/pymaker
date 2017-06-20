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

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.sai import Tub
from api.sai.Lpc import Lpc
from api.token.ERC20Token import ERC20Token
from keepers.arbitrage.Conversion import Conversion


class LpcTakeEthConversion(Conversion):
    # TODO we make an assumption that the same feed is used for Tub and Lpc
    # as we don't check which token is ref and which is alt here
    def __init__(self, tub: Tub, lpc: Lpc):
        self.tub = tub
        self.lpc = lpc
        self.lpc.alt()
        rate = (Ray.from_number(1) / Ray(lpc.tag())) / Ray(lpc.gap())
        #TODO we always leave 0.001 in the liquidity pool, in case of some rounding errors
        max_entry_sai = Wad.max((ERC20Token(web3=tub.web3, address=tub.gem()).balance_of(lpc.address) / Wad(rate)) - Wad.from_number(0.001), Wad.from_number(0))
        super().__init__(from_currency='SAI',
                         to_currency='ETH',
                         rate=rate,
                         min_from_amount=Wad.from_number(0),
                         max_from_amount=max_entry_sai,
                         method="lpc-take-eth")

    def perform(self):
        print(f"  Executing take(ETH, '{self.to_amount}') in order to exchange {self.from_amount} SAI to {self.to_amount} ETH")
        take_result = self.lpc.take(self.tub.gem(), self.to_amount)
        if take_result:
            our_address = Address(self.tub.web3.eth.defaultAccount)
            sai_transfer_on_take = next(filter(lambda transfer: transfer.token_address == self.tub.sai() and transfer.from_address == our_address, take_result.transfers))
            eth_transfer_on_take = next(filter(lambda transfer: transfer.token_address == self.tub.gem() and transfer.to_address == our_address, take_result.transfers))
            print(f"  Take was successful, exchanged {sai_transfer_on_take.value} SAI to {eth_transfer_on_take.value} ETH")
            return take_result
        else:
            print(f"  Take failed!")
            return None
