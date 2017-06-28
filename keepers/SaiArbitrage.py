#!/usr/bin/env python3
#
# This file is part of Maker Keeper Framework.
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
import functools
import time
from _ast import List
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
from keepers.arbitrage.Conversion import Conversion
from keepers.arbitrage.OpportunityFinder import OpportunityFinder
from keepers.arbitrage.conversions.LpcTakeEthConversion import LpcTakeEthConversion
from keepers.arbitrage.conversions.LpcTakeSaiConversion import LpcTakeSaiConversion
from keepers.arbitrage.conversions.OasisTakeConversion import OasisTakeConversion
from keepers.arbitrage.conversions.TubBoomConversion import TubBoomConversion
from keepers.arbitrage.conversions.TubBustConversion import TubBustConversion
from keepers.arbitrage.conversions.TubExitConversion import TubExitConversion
from keepers.arbitrage.conversions.TubJoinConversion import TubJoinConversion


class SaiArbitrage(Keeper):
    def print_introduction(self):
        print(f"Operating as {self.our_address}")

    def setup_allowances(self):
        print(f"Verifying allowances...")
        self.setup_allowance(self.gem, 'W-ETH', self.tub.jar())       # so we can join() and exit()
        self.setup_allowance(self.skr, 'SKR', self.tub.jar())
        self.setup_allowance(self.skr, 'SKR', self.tub.pit())         # so we can boom() and bust()
        self.setup_allowance(self.sai, 'SAI', self.tub.pit())
        self.setup_allowance(self.sai, 'SAI', self.lpc.address)       # so we can take() W-ETH and SAI from Lpc
        self.setup_allowance(self.gem, 'W-ETH', self.lpc.address)
        self.setup_allowance(self.gem, 'W-ETH', self.market.address)  # so we can take orders on OasisDEX
        self.setup_allowance(self.skr, 'SKR', self.market.address)
        self.setup_allowance(self.sai, 'SAI', self.market.address)

    def setup_allowance(self, token, token_name, address):
        minimum_allowance = Wad(2**128-1)
        target_allowance = Wad(2**256-1)
        if token.allowance_of(self.our_address, address) < minimum_allowance:
            print(f"  Raising {token_name} allowance for {address}")
            token.approve(address, target_allowance)

    def tub_conversions(self):
        return [TubJoinConversion(self.tub),
                TubExitConversion(self.tub),
                TubBoomConversion(self.tub),
                TubBustConversion(self.tub)]

    def lpc_conversions(self):
        return [LpcTakeEthConversion(self.tub, self.lpc),
                LpcTakeSaiConversion(self.tub, self.lpc)]

    def otc_offers(self, tokens):
        offers = [self.market.get_offer(offer_id + 1) for offer_id in range(self.market.get_last_offer_id())]
        offers = [offer for offer in offers if offer is not None]
        return [offer for offer in offers if offer.sell_which_token in tokens and offer.buy_which_token in tokens]

    def otc_conversions(self, tokens):
        return list(map(lambda offer: OasisTakeConversion(self.tub, self.market, offer), self.otc_offers(tokens)))

    def all_conversions(self):
        return self.tub_conversions() + self.lpc_conversions() + self.otc_conversions([self.sai, self.skr, self.gem])

    def first_opportunity(self, opportunities):
        if len(opportunities) > 0: return opportunities[0]
        return None

    def print_balances(self):
        print(f"Keeper token balances are: {str(self.gem.balance_of(self.our_address)).rjust(26)} W-ETH")
        print(f"                           {str(self.skr.balance_of(self.our_address)).rjust(26)} SKR")
        print(f"                           {str(self.sai.balance_of(self.our_address)).rjust(26)} SAI")

    def process(self):
        print(f"")
        print(f"")
        print(f"Processing (@ {datetime.datetime.now()})")
        print(f"")
        self.print_balances()
        print(f"")

        # We find all arbitrage opportunities, they can still not bring us the profit we expect them to
        # but it is convenient to list them for monitoring purposes. So that we know the keeper actually
        # found an arbitrage opportunity.
        conversions = self.all_conversions()
        opportunities = OpportunityFinder(conversions=conversions).find_opportunities('SAI', self.maximum_engagement)
        opportunities = filter(lambda opportunity: opportunity.total_rate() > Ray.from_number(1.000001), opportunities)
        opportunities = filter(lambda opportunity: opportunity.profit() > Wad.from_number(0), opportunities)
        opportunities = list(sorted(opportunities, key=lambda opportunity: opportunity.net_profit(), reverse=True))

        if len(opportunities) == 0:
            print(f"No opportunities found. No worries, I will try again.")
            return
        else:
            print(f"Found {len(opportunities)} profit opportunities, here they are:")
            for opportunity in opportunities:
                print(str(opportunity) + "\n")

        # At this point we only leave out these opportunities, that bring us the desired profit.
        # We pick the first of them, the one that brings us the best profit.
        opportunities = list(filter(lambda opportunity: opportunity.net_profit() > self.minimum_profit, opportunities))
        best_opportunity = self.first_opportunity(opportunities)

        if best_opportunity is None:
            print(f"No opportunity is profitable enough so none of them will get executed")
            return

        print("This opportunity will bring us the best profit and will get executed:")
        print(str(best_opportunity))
        print("")

        all_transfers = []

        for index, conversion in enumerate(best_opportunity.conversions, start=1):
            print(f"Step {index}/{len(best_opportunity.conversions)}:")
            receipt = conversion.execute()
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
        parser.add_argument("--minimum-profit", help="Minimum profit in SAI from one arbitrage operation (default: 0.5)", default=0.01, type=float)
        parser.add_argument("--maximum-engagement", help="Maximum engagement in SAI in one arbitrage operation (default: 1000)", default=1000, type=float)
        args = parser.parse_args()

        config = Config()

        web3 = Web3(HTTPProvider(endpoint_uri=f"http://{args.rpc_host}:{args.rpc_port}"))
        web3.eth.defaultAccount = args.eth_from #TODO allow to use ETH_FROM env variable

        self.our_address = Address(args.eth_from)
        self.tub_address = Address(config.get_contract_address("saiTub"))
        self.tap_address = Address(config.get_contract_address("saiTap"))
        self.top_address = Address(config.get_contract_address("saiTop"))
        self.tub = Tub(web3=web3, address_tub=self.tub_address, address_tap=self.tap_address, address_top=self.top_address)
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
        print(f"")

        self.print_introduction()
        self.setup_allowances()

        while True:
            self.process()
            time.sleep(args.frequency)


if __name__ == '__main__':
    SaiArbitrage()
