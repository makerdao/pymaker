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
from keepers.arbitrage.Conversion import Conversion


class TubJoinConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(from_currency='ETH',
                         to_currency='SKR',
                         rate=(Ray.from_number(1) / tub.per()),
                         min_from_amount=Wad.from_number(0),
                         max_from_amount=Wad.from_number(1000000), #1 mio ETH = infinity ;)
                         method="tub-join")

    def perform(self):
        print(f"  Executing join('{self.from_amount}') in order to exchange {self.from_amount} ETH to {self.to_amount} SKR")
        join_result = self.tub.join(self.from_amount)
        if join_result:
            our_address = Address(self.tub.web3.eth.defaultAccount)
            eth_transfer_on_bust = next(filter(lambda transfer: transfer.token_address == self.tub.gem() and transfer.from_address == our_address, join_result.transfers))
            skr_transfer_on_bust = next(filter(lambda transfer: transfer.token_address == self.tub.skr() and transfer.to_address == our_address, join_result.transfers))
            print(f"  Join was successful, exchanged {eth_transfer_on_bust.value} ETH to {skr_transfer_on_bust.value} SKR")
            return join_result
        else:
            print(f"  Join failed!")
            return None
