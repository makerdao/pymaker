#!/usr/bin/env python3

import argparse
import json

import time

from auctions.AuctionEngine import AuctionEngine
from auctions.BasicForwardAuctionStrategy import BasicForwardAuctionStrategy
from contracts.Address import Address
from contracts.DSToken import DSToken
from contracts.ERC20Token import ERC20Token
from contracts.Wad import Wad
from contracts.auctions.AuctionManager import AuctionManager

from web3 import HTTPProvider
from web3 import Web3

from contracts.sai.Tub import Tub

parser = argparse.ArgumentParser(description='Tub biter keeper.')
parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
parser.add_argument("--frequency", help="Frequency of periodical checking of existing auctions (in seconds) (default: 60)", default=60, type=int)
parser.add_argument("--tub", help="Ethereum address of the Tub", required=True, type=str)
parser.add_argument("--trader", help="Ethereum address of the trader ie. the biter", required=True, type=str)
args = parser.parse_args()

with open('addresses.json') as data_file:
    network = "kovan"
    addresses = json.load(data_file)

web3 = Web3(HTTPProvider(endpoint_uri=f"http://{args.rpc_host}:{args.rpc_port}"))
web3.eth.defaultAccount = args.trader

tub_address = Address(args.tub)
tub = Tub(web3=web3, address=tub_address)
trader_address = Address(args.trader)

while True:
    for cup_id in range(1, tub.cupi()+1):
        if not tub.safe(cup_id):
            print(f"Cup {cup_id} is not safe, biting it")
            tub.bite(cup_id)
        else:
            print(f"Cup {cup_id} is safe")

    time.sleep(args.frequency)


# for key, value in addresses[network].items():
#     ERC20Token.register_token(Address(value), key)
#
# strategy = BasicForwardAuctionStrategy(dai_token, mkr_token, args.mkr_dai_rate, args.step, Wad(args.minimal_mkr_bid * 1000000000000000000))
# engine = AuctionEngine(auction_manager, trader_address, strategy, args.frequency)
# engine.start()
