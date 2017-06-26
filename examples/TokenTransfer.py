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

from api.Address import Address
from api.Wad import Wad
from api.sai.Tub import Tub
from api.token.ERC20Token import ERC20Token

web3 = Web3(HTTPProvider(endpoint_uri=f"http://localhost:8545"))
web3.eth.defaultAccount = "0x002ca7F9b416B2304cDd20c26882d1EF5c53F611"

our_address = Address(web3.eth.defaultAccount)
destination_address = Address("0x0061f1dbAf1e1B2E412A75D3eD6B48c3D7412D35")
tub = Tub(web3=web3,
          addressTub=Address('0x15a106e4767c8725182a3151311d6f7ff753ab5b'),
          addressTap=Address('0x4194db843e095f7302da21b50f74629db788f4dd'),
          addressTop=Address('0xa75727ef1ae5bf29f11bbd8fec0bca4b9dd54203'))
sai = ERC20Token(web3=web3, address=tub.sai())

print(f"Source balance before the transfer is {sai.balance_of(our_address)} SAI")
print(f"Destination balance before the transfer is {sai.balance_of(destination_address)} SAI")
print(f"")
print(f"Attempting to transfer 10 SAI...")

if sai.transfer(destination_address, Wad.from_number(10)):
    print(f"Transfer was successful")
    print(f"")
    print(f"Source balance after the transfer is {sai.balance_of(our_address)} SAI")
    print(f"Destination balance after the transfer is {sai.balance_of(destination_address)} SAI")
else:
    print(f"Transfer failed. Check if you have enough SAI balance.")
