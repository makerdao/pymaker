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

from web3 import HTTPProvider
from web3 import Web3

from api import Address
from api.token import ERC20Token
from api.numeric import Wad
from api.sai.Lpc import Lpc
from api.sai.Tub import Tub

web3 = Web3(HTTPProvider(endpoint_uri=f"http://localhost:8545"))
web3.eth.defaultAccount = "0x002ca7F9b416B2304cDd20c26882d1EF5c53F611"

our_address = Address(web3.eth.defaultAccount)
tub = Tub(web3=web3,
          address_tub=Address('0xc349a197c9c3200411094adec82972a2b921c6e2'),
          address_tap=Address('0x3d9a8aa3753bab869b1cc58063063773da54bd66'),
          address_top=Address('0x66174cf99acdb1a5568186a55827b2aac56275e1'))
lpc = Lpc(web3=web3, address=Address('0x421943ce89b6d0daf0128aafc679079050aa0c1e'))
sai = ERC20Token(web3=web3, address=tub.sai())
gem = ERC20Token(web3=web3, address=tub.gem())

# Print our SAI and GEM (W-ETH) balance
print(f"Our balance before the exchange is: {sai.balance_of(our_address)} SAI")
print(f"                                    {gem.balance_of(our_address)} W-ETH")
print(f"")
print(f"Attempting to get 10 SAI in exchange for W-ETH...")
print(f"")

# Perform the exchange (`take()`) via LPC
# Print our balances again afterwards
if lpc.take(tub.sai(), Wad.from_number(10)):
    print(f"Exchange was successful.")
    print(f"Our balance after the exchange is:  {sai.balance_of(our_address)} SAI")
    print(f"                                    {gem.balance_of(our_address)} W-ETH")
else:
    print(f"Exchange failed. Check if you have enough W-ETH balance.")
