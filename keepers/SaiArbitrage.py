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
import datetime
import time

from web3 import HTTPProvider
from web3 import Web3

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.otc.SimpleMarket import SimpleMarket
from api.sai.Lpc import Lpc
from api.sai.Tub import Tub
from api.token.ERC20Token import ERC20Token
from api.feed.DSValue import DSValue
from keepers.Config import Config
from keepers.Keeper import Keeper
from keepers.arbitrage.Conversion import Conversion
from keepers.arbitrage.OpportunityFinder import OpportunityFinder
from keepers.arbitrage.conversions.BustConversion import BustConversion
from keepers.arbitrage.conversions.OasisConversion import OasisConversion


class SaiProcessWoe(Keeper):
    def all_offers(self, market):
        all_offers = [market.get_offer(offer_id) for offer_id in range(1, market.get_last_offer_id()+1)]
        return [offer for offer in all_offers if offer is not None]

    def filter_by_token_pair(self, offers, sell_which_token, buy_which_token):
        return [offer for offer in offers if offer.sell_which_token == sell_which_token and offer.buy_which_token == buy_which_token]

    def sell_to_buy_price(self, offer):
        return Ray(offer.sell_how_much)/Ray(offer.buy_how_much)

    def buy_to_sell_price(self, offer):
        return Ray(offer.sell_how_much)/Ray(offer.buy_how_much)

    def first_offer(self, offers):
        if len(offers) > 0: return offers[0]
        return None

    def setup_allowances(self):
        for address in [self.market.address, self.tub.address]:
            self.setup_allowance(self.skr, 'SKR', address)
            self.setup_allowance(self.sai, 'SAI', address)
            self.setup_allowance(self.gem, 'ETH', address)
        self.setup_allowance(self.sai, 'SAI', self.lpc.address)
        self.setup_allowance(self.gem, 'ETH', self.lpc.address)

    def setup_allowance(self, token, token_name, address):
        minimum_allowance = Wad(2**248-1)
        target_allowance = Wad(2**256-1)
        if token.allowance_of(self.our_address, address) < minimum_allowance:
            print(f"Raising {token_name} allowance for {address}")
            token.approve(address, target_allowance)


    def available_conversions(self):
        conversions = [
            # join/exit on the Tub
            # unlimited, the only limit is the amount of tokens we have
            # rate is Tub.per()
            # Conversion("ETH", "SKR", Ray.from_number(1), 100, "tub-join"),
            # Conversion("SKR", "ETH", Ray.from_number(1), 100, "tub-exit"),

            # take on the Lpc
            # limited, depends on how many tokens in the pool, but we can check it
            # rate is Lpc.tag() or 1/Lpc.tag(), depending on the direction
            # Conversion("ETH", "SAI", Ray.from_number(362.830), 100, "lpc-take-SAI"),
            # Conversion("SAI", "ETH", Ray.from_number(1/float("362.830")), 100, "lpc-take-ETH"),

            # woe in the Tub
            # limited, depends on how much woe in the Tub (after "mending")
            # rate is 1/Tub.tag()
            # Conversion("SAI", "SKR", Ray.from_number(1/float("362.830")), 100, "tub-bust"), #real data ["0.002756111677645"] []

            # joy in the Tub
            # limited, depends on how much joy in the Tub (after "mending")
            # rate is Tub.tag()
            # Conversion("SKR", "SAI", "362.830", 0.6, "tub-boom"),

            # plus all the orders from Oasis
            # Conversion("SKR", "SAI", Ray.from_number(363.830), 100, "oasis-takeOrder-121"), #real data
        ]
        conversions.append(BustConversion(self.tub))

        # We list all active orders on OasisDEX and filter on the SAI/SKR pair
        offers = self.all_offers(self.market)
        offers = self.filter_by_token_pair(offers, self.sai, self.skr)\
                 + self.filter_by_token_pair(offers, self.skr, self.sai) \
                 + self.filter_by_token_pair(offers, self.gem, self.sai) \
                 + self.filter_by_token_pair(offers, self.sai, self.gem) \
                 + self.filter_by_token_pair(offers, self.gem, self.skr) \
                 + self.filter_by_token_pair(offers, self.skr, self.gem)
        for offer in offers:
            conversions.append(OasisConversion(self.tub, self.market, offer))

        return conversions


    def process(self):
        print(f"")
        self.setup_allowances()
        print(f"Processing (@ {datetime.datetime.now()})")

        opportunities = OpportunityFinder(conversions=self.available_conversions()).opportunities('SAI')
        opportunities = filter(lambda opportunity: opportunity.total_rate() > Ray.from_number(1.0), opportunities)
        for opportunity in opportunities:
            print(repr(opportunity))

    def __init__(self):
        parser = argparse.ArgumentParser(description='SaiProcessWoe keeper. Arbitrages on SAI/SKR price via bust().')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
        parser.add_argument("--frequency", help="Frequency of checking for arbitrage opportunities (default: 5)", default=5, type=float)
        parser.add_argument("--minimum-order-size", help="Minimum order size in SAI (default: 50)", default=50, type=float)
        parser.add_argument("--minimum-profit", help="Minimum profit in SAI (default: 1)", default=1, type=float)
        args = parser.parse_args()

        config = Config()

        web3 = Web3(HTTPProvider(endpoint_uri=f"http://{args.rpc_host}:{args.rpc_port}"))
        web3.eth.defaultAccount = args.eth_from #TODO allow to use ETH_FROM env variable

        self.our_address = Address(args.eth_from)
        self.tub_address = Address(config.get_contract_address("saiTub"))
        self.tub = Tub(web3=web3, address=self.tub_address)
        self.tip = DSValue(web3=web3, address=self.tub.tip())
        self.skr = ERC20Token(web3=web3, address=self.tub.skr())
        self.sai = ERC20Token(web3=web3, address=self.tub.sai())
        self.gem = ERC20Token(web3=web3, address=self.tub.gem())

        self.lpc_address = Address(config.get_contract_address("saiLpc"))
        self.lpc = Lpc(web3=web3, address=self.lpc_address)

        self.market_address = Address(config.get_contract_address("otc"))
        self.market = SimpleMarket(web3=web3, address=self.market_address)

        self.minimum_order_size = args.minimum_order_size
        self.minimum_profit = args.minimum_profit

        print(f"")
        print(f"SaiArbitrage keeper")
        print(f"--------------------")

        while True:
            self.process()
            time.sleep(args.frequency)


if __name__ == '__main__':
    SaiProcessWoe().run()





