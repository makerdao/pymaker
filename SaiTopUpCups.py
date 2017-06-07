#!/usr/bin/env python3

import argparse
import time

from Config import Config

from web3 import HTTPProvider
from web3 import Web3

from contracts.Address import Address
from contracts.sai.Tub import Tub

parser = argparse.ArgumentParser(description='Sai cups top-up keeper. Locks additional collateral in cups if they gett close to liquidation threshold.')
parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
parser.add_argument("--frequency", help="Frequency of checking for unsafe cups (in seconds) (default: 60)", default=60, type=int)
args = parser.parse_args()

config = Config()

web3 = Web3(HTTPProvider(endpoint_uri=f"http://{args.rpc_host}:{args.rpc_port}"))
web3.eth.defaultAccount = args.eth_from #TODO allow to use ETH_FROM env variable

tub_address = Address(config.get_contract_address("saiTub"))
tub = Tub(web3=web3, address=tub_address)

#TODO this is just some experimental code to test
print("TODO")
print(tub.air())
print(tub.axe())
print(tub.fix())
print(tub.fog())
print(tub.tag())
print(tub.tip())
print(tub.cups(1))
print(tub.tab(1))
print("TODO")


for cup_id in range(1, tub.cupi()+1):
    #TODO as we do cups(...) and tab(...) in two separate calls, there is a slight chance that they might get evaulated
    #TODO on two different blocks, which will make the collateralization ratio calculation wrong
    cup = tub.cups(cup_id)
    pro = cup.ink*(tub.per()*tub.tag())
    tab = tub.tab(cup_id)
    collateralization_ratio = pro / tab

    print(f"Cup {cup_id} has collateralization ratio {collateralization_ratio}")
