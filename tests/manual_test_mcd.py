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


import sys
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.deployment import DssDeployment
from pymaker.keys import register_keys
from pymaker.numeric import Wad


web3 = Web3(HTTPProvider(endpoint_uri="http://0.0.0.0:8545",
                         request_kwargs={"timeout": 10}))
web3.eth.defaultAccount = sys.argv[1]   # ex: 0x0000000000000000000000000000000aBcdef123
register_keys(web3, [sys.argv[2]])      # ex: key_file=~keys/default-account.json,pass_file=~keys/default-account.pass

mcd = DssDeployment.from_json(web3=web3, conf=open("config/kovan-addresses.json", "r").read())
our_address = Address(web3.eth.defaultAccount)

# Choose the desired collateral; in this case we'll wrap some Eth
collateral = mcd.collaterals['ETH-A']
ilk = collateral.ilk
collateral_amount = Wad.from_number(0.03)
collateral.gem.deposit(collateral_amount).transact()

# Add collateral and allocate the desired amount of Dai
collateral.approve(our_address)
assert collateral.adapter.join(our_address, collateral_amount).transact()
dai_amount = Wad.from_number(0.153)
mcd.vat.frob(ilk, our_address, dink=collateral_amount, dart=Wad(0)).transact()
mcd.vat.frob(ilk, our_address, dink=Wad(0), dart=dai_amount).transact()
print(f"CDP Dai balance before withdrawal: {mcd.vat.dai(our_address)}")

# Mint and withdraw our Dai
mcd.approve_dai(our_address)
mcd.dai_adapter.exit(our_address, dai_amount).transact()
print(f"CDP Dai balance after withdrawal:  {mcd.vat.dai(our_address)}")

# Repay (and burn) our Dai
assert mcd.dai_adapter.join(our_address, dai_amount).transact()
print(f"CDP Dai balance after repayment:   {mcd.vat.dai(our_address)}")

# Withdraw our collateral
mcd.vat.frob(ilk, our_address, dink=Wad(0), dart=dai_amount*-1).transact()
mcd.vat.frob(ilk, our_address, dink=collateral_amount*-1, dart=Wad(0)).transact()
collateral.adapter.exit(our_address, collateral_amount).transact()
print(f"CDP Dai balance w/o collateral:    {mcd.vat.dai(our_address)}")
