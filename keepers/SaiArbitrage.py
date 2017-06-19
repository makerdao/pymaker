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
from functools import reduce

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
from keepers.arbitrage.OpportunityFinder import OpportunityFinder
from keepers.arbitrage.conversions.BoomConversion import BoomConversion
from keepers.arbitrage.conversions.BustConversion import BustConversion
from keepers.arbitrage.conversions.ExitConversion import ExitConversion
from keepers.arbitrage.conversions.JoinConversion import JoinConversion
from keepers.arbitrage.conversions.OasisConversion import OasisConversion


class SaiArbitrage(Keeper):
    def all_offers(self, market):
        all_offers = [market.get_offer(offer_id) for offer_id in range(1, market.get_last_offer_id()+1)]
        return [offer for offer in all_offers if offer is not None]

    def filter_by_token_pair(self, offers, sell_which_token, buy_which_token):
        return [offer for offer in offers if offer.sell_which_token == sell_which_token and offer.buy_which_token == buy_which_token]

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
        conversions = []
        conversions.append(JoinConversion(self.tub))
        conversions.append(ExitConversion(self.tub))
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

    def first_opportunity(self, opportunities):
        if len(opportunities) > 0: return opportunities[0]
        return None

    def process(self):
        print(f"")
        print(f"")
        print(f"Processing (@ {datetime.datetime.now()})")
        print(f"")

        conversions = self.available_conversions()
        opportunities = OpportunityFinder(conversions=conversions).find_opportunities('SAI', self.maximum_engagement)
        opportunities = filter(lambda opportunity: opportunity.total_rate() > Ray.from_number(1.000001), opportunities)
        opportunities = list(sorted(opportunities, key=lambda opportunity: opportunity.gain(), reverse=True))

        if len(opportunities) == 0:
            print(f"No opportunities found. No worries, I will try again.")
            return
        else:
            print(f"Found {len(opportunities)} profit opportunities, here they are:")
            for opportunity in opportunities:
                print(str(opportunity) + "\n")

        profitable_opportunities = list(filter(lambda opportunity: opportunity.gain() > self.minimum_profit, opportunities))
        best_opportunity = self.first_opportunity(profitable_opportunities)

        if best_opportunity is None:
            print(f"No opportunity is profitable enough so none of them will get executed")
            return

        print("This opportunity will bring us the best profit and will get executed:")
        print(str(best_opportunity))
        print("")

        all_transfers = []

        for index, conversion in enumerate(best_opportunity.conversions, start=1):
            print(f"Step {index}/{len(best_opportunity.conversions)}:")
            receipt = conversion.perform()
            if receipt is None:
                print(f"")
                print(f"Interrupting the process...")
                print(f"Will start over from scratch in the next round.")
                return
            else:
                print(f"  TxHash: {receipt.transaction_hash}")
                all_transfers += receipt.transfers

        def sum_of_wads(list_of_wads):
            return reduce(Wad.__add__, list_of_wads, Wad.from_number(0))

        print(f"")
        print(f"All steps executed successfully. The profit we made on this opportunity is:")
        skr_in = filter(lambda transfer: transfer.token_address == self.tub.skr() and transfer.to_address == self.our_address, all_transfers)
        skr_out = filter(lambda transfer: transfer.token_address == self.tub.skr() and transfer.from_address == self.our_address, all_transfers)
        sai_in = filter(lambda transfer: transfer.token_address == self.tub.sai() and transfer.to_address == self.our_address, all_transfers)
        sai_out = filter(lambda transfer: transfer.token_address == self.tub.sai() and transfer.from_address == self.our_address, all_transfers)
        eth_in = filter(lambda transfer: transfer.token_address == self.tub.gem() and transfer.to_address == self.our_address, all_transfers)
        eth_out = filter(lambda transfer: transfer.token_address == self.tub.gem() and transfer.from_address == self.our_address, all_transfers)
        print(f"  {sum_of_wads(transfer.value for transfer in skr_in) - sum_of_wads(transfer.value for transfer in skr_out)} SKR")
        print(f"  {sum_of_wads(transfer.value for transfer in sai_in) - sum_of_wads(transfer.value for transfer in sai_out)} SAI")
        print(f"  {sum_of_wads(transfer.value for transfer in eth_in) - sum_of_wads(transfer.value for transfer in eth_out)} ETH")


    def __init__(self):
        parser = argparse.ArgumentParser(description='SaiArbitrage keeper.')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
        parser.add_argument("--frequency", help="Frequency of checking for arbitrage opportunities (default: 5)", default=5, type=float)
        parser.add_argument("--minimum-profit", help="Minimum profit in SAI from one arbitrage operation (default: 0.5)", default=0.5, type=float)
        parser.add_argument("--maximum-engagement", help="Maximum engagement in SAI in one arbitrage operation (default: 1000)", default=1000, type=float)
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

        self.minimum_profit = Wad.from_number(args.minimum_profit)
        self.maximum_engagement = Wad.from_number(args.maximum_engagement)

        print(f"")
        print(f"SaiArbitrage keeper")
        print(f"-------------------")

        self.setup_allowances()

        while True:
            self.process()
            time.sleep(args.frequency)


if __name__ == '__main__':
    SaiArbitrage()
