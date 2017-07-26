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

import json
import urllib.request

from web3 import HTTPProvider
from web3 import Web3

from api import Address
from api.feed import DSValue
from api.numeric import Wad


def cryptocompare_rate() -> Wad:
    with urllib.request.urlopen("https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD") as url:
        data = json.loads(url.read().decode())
        return Wad.from_number(data['USD'])


def difference(wad1: Wad, wad2: Wad) -> Wad:
    if wad1 > wad2:
        return wad1 - wad2
    else:
        return wad2 - wad1


web3 = Web3(HTTPProvider(endpoint_uri=f"http://localhost:8545"))
web3.eth.defaultAccount = "0x002ca7F9b416B2304cDd20c26882d1EF5c53F611"

dsvalue_address = Address('0x038b3d8288df582d57db9be2106a27be796b0daf')
dsvalue = DSValue(web3=web3, address=dsvalue_address)

dsvalue_value = Wad(dsvalue.read_as_int())
cryptocompare_value = cryptocompare_rate()
threshold = Wad.from_number(0.25)

print(f"Value in DSValue is   : {dsvalue_value} USD/ETH")
print(f"Cryptocompare value is: {cryptocompare_value} USD/ETH")
print(f"")

if difference(dsvalue_value, cryptocompare_value) > threshold:
    print(f"Difference is >= {threshold}, will update")
    if dsvalue.poke_with_int(cryptocompare_value.value):
        dsvalue_value = Wad(dsvalue.read_as_int())
        print(f"Successfully updated the DSValue value, which is now {dsvalue_value} USD/ETH")
    else:
        print(f"Updating the DSValue value failed")
else:
    print(f"Difference is small enough, no need to update")
