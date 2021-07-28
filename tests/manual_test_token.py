# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2021 EdNoepel
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

import logging
import os
import sys
import time

from pymaker import Address, web3_via_http
from pymaker.keys import register_keys
from pymaker.numeric import Wad
from pymaker.token import DSToken

logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.DEBUG)
# reduce logspew
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger("web3").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("requests").setLevel(logging.INFO)

endpoint_uri = os.environ['ETH_RPC_URL']
web3 = web3_via_http(endpoint_uri, timeout=10)
print(web3.clientVersion)

"""
Please set environment ETH_RPC_URL to your Ethereum node URI

Argument:           Reqd?   Example:
Ethereum address    yes     0x0000000000000000000000000000000aBcdef123
Private key         yes     key_file=~keys/default-account.json,pass_file=~keys/default-account.pass
Action              yes     token address to mint existing DSToken, symbol to deploy a new token 
"""

web3.eth.defaultAccount = sys.argv[1]
register_keys(web3, [sys.argv[2]])
our_address = Address(web3.eth.defaultAccount)
action = sys.argv[3]

if action.startswith("0x"):
    token = DSToken(web3, Address(action))
    token.mint_to(our_address, Wad.from_number(100)).transact()
else:
    symbol = action
    assert len(symbol) < 6  # Most token symbols are under 6 characters; were you really trying to deploy a new token?
    token = DSToken.deploy(web3, symbol)
    print(f"{symbol} token deployed to {token.address.address}")
