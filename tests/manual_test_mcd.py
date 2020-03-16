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

import os
import sys
from pprint import pprint
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.auctions import Flipper, Flapper, Flopper
from pymaker.deployment import DssDeployment
from pymaker.keys import register_keys
from pymaker.numeric import Wad

endpoint_uri = f"{os.environ['SERVER_ETH_RPC_HOST']}:{os.environ['SERVER_ETH_RPC_PORT']}"
web3 = Web3(HTTPProvider(endpoint_uri=endpoint_uri, request_kwargs={"timeout": 10}))
web3.eth.defaultAccount = sys.argv[1]   # ex: 0x0000000000000000000000000000000aBcdef123
register_keys(web3, [sys.argv[2]])      # ex: key_file=~keys/default-account.json,pass_file=~keys/default-account.pass

mcd = DssDeployment.from_node(web3)
our_address = Address(web3.eth.defaultAccount)

# Choose the desired collateral; in this case we'll wrap some Eth
collateral = mcd.collaterals['ETH-A']
ilk = collateral.ilk

# This is a safe amount of collateral (as of 2020.03.11) to draw 20 Dai
collateral_amount = Wad.from_number(0.2)
if collateral.gem.balance_of(our_address) > collateral_amount:
    collateral.gem.deposit(collateral_amount).transact()

    # Add collateral and allocate the desired amount of Dai
    collateral.approve(our_address)
    assert collateral.adapter.join(our_address, collateral_amount).transact()
    dai_amount = Wad.from_number(0.153)
    mcd.vat.frob(ilk, our_address, dink=collateral_amount, dart=Wad(0)).transact()
    mcd.vat.frob(ilk, our_address, dink=Wad(0), dart=dai_amount).transact()
    print(f"Dai balance before withdrawal: {mcd.vat.dai(our_address)}")

    # Mint and withdraw our Dai
    mcd.approve_dai(our_address)
    mcd.dai_adapter.exit(our_address, dai_amount).transact()
    print(f"Dai balance after withdrawal:  {mcd.vat.dai(our_address)}")

    # Repay (and burn) our Dai
    assert mcd.dai_adapter.join(our_address, dai_amount).transact()
    print(f"Dai balance after repayment:   {mcd.vat.dai(our_address)}")

    # Withdraw our collateral
    mcd.vat.frob(ilk, our_address, dink=Wad(0), dart=dai_amount*-1).transact()
    mcd.vat.frob(ilk, our_address, dink=collateral_amount*-1, dart=Wad(0)).transact()
    collateral.adapter.exit(our_address, collateral_amount).transact()
    print(f"Dai balance w/o collateral:    {mcd.vat.dai(our_address)}")

print(f"Collateral balance: {mcd.vat.gem(ilk, our_address)}")
