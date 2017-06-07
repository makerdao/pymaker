#!/usr/bin/env python3

import argparse

from Config import Config
from auctions.AuctionEngine import AuctionEngine
from auctions.BasicForwardAuctionStrategy import BasicForwardAuctionStrategy
from contracts.Address import Address
from contracts.DSToken import DSToken
from contracts.ERC20Token import ERC20Token
from contracts.Wad import Wad
from contracts.auctions.AuctionManager import AuctionManager

from web3 import HTTPProvider
from web3 import Web3

parser = argparse.ArgumentParser(description='Maker BuyAndBurn keeper. Buys DAI for MKR on forward auctions.')
parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
parser.add_argument("--frequency", help="Frequency of periodical checking of existing auctions (in seconds) (default: 60)", default=60, type=int)
parser.add_argument("--mkr-dai-rate", help="Target MKR/DAI rate", required=True, type=float)
parser.add_argument("--minimal-mkr-bid", help="Minimal amount of MKR you want to bid", required=True, type=float)
parser.add_argument("--step", help="Incremental step towards the maximum price (value between 0 and 1)", required=True, type=float)
args = parser.parse_args()

config = Config()

web3 = Web3(HTTPProvider(endpoint_uri=f"http://{args.rpc_host}:{args.rpc_port}"))
web3.eth.defaultAccount = args.eth_from #TODO allow to use ETH_FROM env variable

auction_manager_address = Address(config.contracts()["auctionManager"])
auction_manager = AuctionManager(web3=web3, address=auction_manager_address, is_splitting=True)
trader_address = Address(args.eth_from)
dai_address = ERC20Token.token_address_by_name("DAI")
dai_token = ERC20Token(web3=web3, address=dai_address)
mkr_address = ERC20Token.token_address_by_name("MKR")
mkr_token = DSToken(web3=web3, address=mkr_address)

strategy = BasicForwardAuctionStrategy(dai_token, mkr_token, args.mkr_dai_rate, args.step, Wad(args.minimal_mkr_bid * 1000000000000000000))
engine = AuctionEngine(auction_manager, trader_address, strategy, args.frequency)
engine.start()
