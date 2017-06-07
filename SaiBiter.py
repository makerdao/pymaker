#!/usr/bin/env python3

import argparse
import time

from Config import Config

from web3 import HTTPProvider
from web3 import Web3

from contracts.Address import Address
from contracts.sai.Tub import Tub

parser = argparse.ArgumentParser(description='Sai biter keeper. Bites unsafe cups.')
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

while True:
    for cup_id in range(1, tub.cupi()+1):
        if not tub.safe(cup_id):
            print(f"Cup {cup_id} is not safe, biting it")
            tub.bite(cup_id)
        else:
            print(f"Cup {cup_id} is safe")
    time.sleep(args.frequency)
    #TODO what about recovering CDPs?
