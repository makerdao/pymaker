# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 grandizzy
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


import sys
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.deployment import DssDeployment
from pymaker.keys import register_keys
from pymaker.numeric import Wad
from pymaker.dsr import Dsr


web3 = Web3(HTTPProvider(endpoint_uri="http://0.0.0.0:8545",
                         request_kwargs={"timeout": 10}))
web3.eth.defaultAccount = sys.argv[1]   # ex: 0x0000000000000000000000000000000aBcdef123
register_keys(web3, [sys.argv[2]])      # ex: key_file=~keys/default-account.json,pass_file=~keys/default-account.pass

mcd = DssDeployment.from_network(web3, "kovan")
our_address = Address(web3.eth.defaultAccount)
print(our_address)

dsr_client = Dsr(mcd, our_address)

print(f"Chi: {dsr_client.chi()}")
print(f"Total DAI: {dsr_client.get_total_dai()}")
print(f"DSR: {dsr_client.dsr()}")

proxy = dsr_client.get_proxy()
print(f"Has Proxy: {dsr_client.has_proxy()}")

if not dsr_client.has_proxy():
    dsr_client.build_proxy().transact()

proxy = dsr_client.get_proxy()
print(f"Proxy address: {proxy.address.address}")

print(f"Balance: {dsr_client.get_balance(proxy.address)}")

# approve proxy to use 10 DAI from account
dsr_client.mcd.dai.approve(proxy.address, Wad.from_number(10)).transact()

dsr_client.join(Wad.from_number(2.2), proxy).transact()
print(f"Balance: {dsr_client.get_balance(proxy.address)}")

dsr_client.exit(Wad.from_number(1.01), proxy).transact()
print(f"Balance: {dsr_client.get_balance(proxy.address)}")

dsr_client.exit_all(proxy).transact()
print(f"Balance: {dsr_client.get_balance(proxy.address)}")

