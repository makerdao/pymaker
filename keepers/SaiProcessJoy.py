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

import argparse

import time
from web3 import HTTPProvider
from web3 import Web3

from contracts.Address import Address
from contracts.DSValue import DSValue
from contracts.ERC20Token import ERC20Token
from contracts.Ray import Ray
from contracts.Wad import Wad
from contracts.sai.Tub import Tub
from keepers.Config import Config

parser = argparse.ArgumentParser(description='SaiProcessJoy keeper..')
parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
parser.add_argument("--frequency", help="Frequency of checking for arbitrate opportunities for joy (default: 5)", default=5, type=float)
args = parser.parse_args()

config = Config()

web3 = Web3(HTTPProvider(endpoint_uri=f"http://{args.rpc_host}:{args.rpc_port}"))
web3.eth.defaultAccount = args.eth_from #TODO allow to use ETH_FROM env variable

our_address = Address(args.eth_from)
tub_address = Address(config.get_contract_address("saiTub"))
tub = Tub(web3=web3, address=tub_address)
tip = DSValue(web3=web3, address=tub.tip())
skr = ERC20Token(web3=web3, address=tub.skr())
sai = ERC20Token(web3=web3, address=tub.sai())

# TODO
# ^ true. ~My guess would be simultaneously, since if you wait for one to complete first you have an even greater risk of one of them failing and one succeeding.~
# ^ oh actually, ending up with excess Sai is much safer than ending up with excess SKR. So perhaps the sensible option is to do the Sai purchase first (either on Oasis or `boom`, depending on which arb direction we are in), and upon its completion do the Sai sale (either on Oasis or `bust`)


print(f"")
print(f"SaiProcessJoy keeper")
print(f"-------------------")
print(f"")


joy = tub.joy() # in SAI
woe = tub.woe() # in SAI

mendable_amount = Wad.min(joy, woe)
joy -= mendable_amount
woe -= mendable_amount

price = tub.tag() * tub.per()

print(f"PRICE SAI/SKR: {price}")
print(f"JOY: {joy} SAI")

joy_in_skr = joy/(price)
print(f"JOY IN SKR: {joy_in_skr} SKR")

# skr.balance_of()

# // price of wad in sai
# var ret = rmul(wmul(wad, tag()), per());


print("WOE: " + str(woe))



woe_in_skr = Wad.from_number(woe / (price))
print(f"WOE IN SKR: {woe_in_skr} SKR")
