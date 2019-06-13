# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 EdNoepel
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


from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.deployment import DssDeployment
from pymaker.keys import register_keys
from pymaker.numeric import Wad


web3 = Web3(HTTPProvider(endpoint_uri="https://parity0.kovan.makerfoundation.com:8545",
                         request_kwargs={"timeout": 10}))
web3.eth.defaultAccount = "0xC140ce1be1c0edA2f06319d984c404251C59494e"
register_keys(web3,
                  ["key_file=/home/ed/Projects/member-account.json,pass_file=/home/ed/Projects/member-account.pass",
                   "key_file=/home/ed/Projects/kovan-account2.json,pass_file=/home/ed/Projects/kovan-account2.pass"])


mcd = DssDeployment.from_json(web3=web3, conf=open("tests/config/kovan-addresses.json", "r").read())
our_address = Address(web3.eth.defaultAccount)

# Choose the desired collateral; in this case we'll wrap some Eth
collateral = mcd.collaterals[1]
ilk = collateral.ilk
collateral.gem.deposit(Wad.from_number(3)).transact()

# Add collateral and allocate the desired amount of Dai
collateral.adapter.join(our_address, Wad.from_number(3)).transact()
mcd.vat.frob(ilk, our_address, dink=Wad.from_number(3), dart=Wad.from_number(153)).transact()
print(f"CDP Dai balance before withdrawal: {mcd.vat.dai(our_address)}")

# Mint and withdraw our Dai
mcd.dai_adapter.exit(our_address, Wad.from_number(153)).transact()
print(f"CDP Dai balance after withdrawal:  {mcd.vat.dai(our_address)}")

# Repay (and burn) our Dai
assert mcd.dai_adapter.join(our_address, Wad.from_number(153)).transact()
print(f"CDP Dai balance after repayment:   {mcd.vat.dai(our_address)}")

# Withdraw our collateral
mcd.vat.frob(ilk, our_address, dink=Wad(0), dart=Wad.from_number(-153)).transact()
mcd.vat.frob(ilk, our_address, dink=Wad.from_number(-3), dart=Wad(0)).transact()
collateral.adapter.exit(our_address, Wad.from_number(3)).transact()
print(f"CDP Dai balance w/o collateral:    {mcd.vat.dai(our_address)}")