#!/usr/bin/env python3
#
#  This file is part of "maker.py".
# Copyright (C) 2017 MakerDAO
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

from auctions.AuctionEngine import AuctionEngine
from web3 import HTTPProvider
from web3 import Web3

from contracts.Address import Address
from contracts.DSToken import DSToken
from contracts.ERC20Token import ERC20Token
from contracts.Wad import Wad
from contracts.auctions.AuctionManager import AuctionManager
from keepers.Config import Config
from keepers.auctions.BasicForwardAuctionStrategy import BasicForwardAuctionStrategy

parser = argparse.ArgumentParser(description='Dai Buy&Burn keeper. Buys DAI for MKR on forward auctions.')
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

auction_manager_address = Address(config.get_contract_address("auctionManager"))
auction_manager = AuctionManager(web3=web3, address=auction_manager_address, is_splitting=True)
trader_address = Address(args.eth_from)
dai_address = ERC20Token.token_address_by_name("DAI")
dai_token = ERC20Token(web3=web3, address=dai_address)
mkr_address = ERC20Token.token_address_by_name("MKR")
mkr_token = DSToken(web3=web3, address=mkr_address)

strategy = BasicForwardAuctionStrategy(dai_token, mkr_token, args.mkr_dai_rate, args.step, Wad(args.minimal_mkr_bid * 1000000000000000000))
engine = AuctionEngine(auction_manager, trader_address, strategy, args.frequency)
engine.start()
