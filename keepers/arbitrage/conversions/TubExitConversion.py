#!/usr/bin/env python3
#
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
from api.Wad import Wad
from api.sai import Tub
from keepers.arbitrage.Conversion import Conversion


class TubExitConversion(Conversion):
    def __init__(self, tub: Tub):
        self.tub = tub
        super().__init__(from_currency='SKR',
                         to_currency='ETH',
                         rate=tub.per(),
                         min_from_amount=Wad.from_number(0),
                         max_from_amount=Wad.from_number(1000000), #1 mio SKR = infinity ;)
                         method="tub-exit")

    def perform(self):
        print(f"  Executing exit('{self.from_amount}') in order to exchange {self.from_amount} SKR to {self.to_amount} ETH")
        join_result = self.tub.exit(self.from_amount)
        if join_result:
            our_address = Address(self.tub.web3.eth.defaultAccount)
            skr_transfer_on_bust = next(filter(lambda transfer: transfer.token_address == self.tub.skr() and transfer.from_address == our_address, join_result.transfers))
            eth_transfer_on_bust = next(filter(lambda transfer: transfer.token_address == self.tub.gem() and transfer.to_address == our_address, join_result.transfers))
            print(f"  Exit was successful, exchanged {skr_transfer_on_bust.value} SKR to {eth_transfer_on_bust.value} ETH")
            return join_result
        else:
            print(f"  Exit failed!")
            return None
