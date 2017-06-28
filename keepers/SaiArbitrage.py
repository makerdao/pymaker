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
import time

from web3 import HTTPProvider
from web3 import Web3

from api.Address import Address
from api.Ray import Ray
from api.Transfer import Transfer
from api.Wad import Wad
from api.otc.SimpleMarket import SimpleMarket
from api.sai.Lpc import Lpc
from api.sai.Tub import Tub
from api.token.ERC20Token import ERC20Token
from keepers.Config import Config
from keepers.Keeper import Keeper
from keepers.arbitrage.OpportunityFinder import OpportunityFinder
from keepers.arbitrage.conversions.LpcTakeAltConversion import LpcTakeAltConversion
from keepers.arbitrage.conversions.LpcTakeRefConversion import LpcTakeRefConversion
from keepers.arbitrage.conversions.OasisTakeConversion import OasisTakeConversion
from keepers.arbitrage.conversions.TubBoomConversion import TubBoomConversion
from keepers.arbitrage.conversions.TubBustConversion import TubBustConversion
from keepers.arbitrage.conversions.TubExitConversion import TubExitConversion
from keepers.arbitrage.conversions.TubJoinConversion import TubJoinConversion
from keepers.arbitrage.transfer_formatter import TransferFormatter


class SaiArbitrage(Keeper):
    def print_introduction(self):
        print(f"Operating as {self.our_address}")

    def setup_allowances(self):
        self.setup_tub_allowances()
        self.setup_lpc_allowances()
        self.setup_otc_allowances()

    def setup_tub_allowances(self):
        """Approves Tub components so we can call join()/exit() and boom()/bust()"""
        self.setup_allowance(self.gem, self.tub.jar(), 'Tub.jar')
        self.setup_allowance(self.skr, self.tub.jar(), 'Tub.jar')
        self.setup_allowance(self.skr, self.tub.pit(), 'Tub.pit')
        self.setup_allowance(self.sai, self.tub.pit(), 'Tub.pit')

    def setup_lpc_allowances(self):
        """Approves the Lpc so we can exchange WETH and SAI using it"""
        self.setup_allowance(self.gem, self.lpc.address, 'Lpc')
        self.setup_allowance(self.sai, self.lpc.address, 'Lpc')

    def setup_otc_allowances(self):
        """Approves OasisDEX so we can exchange all three tokens (WETH, SAI and SKR)"""
        self.setup_allowance(self.gem, self.otc.address, 'OasisDEX')
        self.setup_allowance(self.sai, self.otc.address, 'OasisDEX')
        self.setup_allowance(self.skr, self.otc.address, 'OasisDEX')

    def setup_allowance(self, token: ERC20Token, spender_address: Address, spender_name: str):
        if token.allowance_of(self.our_address, spender_address) < Wad(2 ** 128 - 1):
            print(f"  Approving {spender_name} ({spender_address}) to access our {token.name()} balance...")
            token.approve(spender_address, Wad(2 ** 256 - 1))

    def tub_conversions(self):
        return [TubJoinConversion(self.tub),
                TubExitConversion(self.tub),
                TubBoomConversion(self.tub),
                TubBustConversion(self.tub)]

    def lpc_conversions(self):
        return [LpcTakeRefConversion(self.lpc),
                LpcTakeAltConversion(self.lpc)]

    def otc_offers(self, tokens):
        offers = [self.otc.get_offer(offer_id + 1) for offer_id in range(self.otc.get_last_offer_id())]
        offers = [offer for offer in offers if offer is not None]
        return [offer for offer in offers if offer.sell_which_token in tokens and offer.buy_which_token in tokens]

    def otc_conversions(self, tokens):
        return list(map(lambda offer: OasisTakeConversion(self.otc, offer), self.otc_offers(tokens)))

    def all_conversions(self):
        return self.tub_conversions() + self.lpc_conversions() + self.otc_conversions([self.sai.address, self.skr.address, self.gem.address])

    def first_opportunity(self, opportunities):
        if len(opportunities) > 0: return opportunities[0]
        return None

    def print_balances(self):
        print(f"Keeper token balances are: {str(self.gem.balance_of(self.our_address)).rjust(26)} W-ETH")
        print(f"                           {str(self.skr.balance_of(self.our_address)).rjust(26)} SKR")
        print(f"                           {str(self.sai.balance_of(self.our_address)).rjust(26)} SAI")
        print(f"")

    def process(self):
        print(f"")
        print(f"")
        print(f"Processing (@ {datetime.datetime.now()})")
        print(f"")
        self.print_balances()

        investment_token = self.tub.sai()

        # We find all arbitrage opportunities, they can still not bring us the profit we expect them to
        # but it is convenient to list them for monitoring purposes. So that we know the keeper actually
        # found an arbitrage opportunity.
        conversions = self.all_conversions()
        opportunities = OpportunityFinder(conversions=conversions).find_opportunities(investment_token, self.maximum_engagement)
        opportunities = filter(lambda opportunity: opportunity.total_rate() > Ray.from_number(1.000001), opportunities)
        opportunities = filter(lambda opportunity: opportunity.profit(investment_token) > Wad.from_number(0), opportunities)
        opportunities = list(sorted(opportunities, key=lambda opportunity: opportunity.net_profit(investment_token), reverse=True))

        if len(opportunities) == 0:
            print(f"No opportunities found. No worries, I will try again.")
            return
        else:
            print(f"Found {len(opportunities)} profit opportunities, here they are:")
            for opportunity in opportunities:
                print(str(opportunity) + "\n")

        # At this point we only leave out these opportunities, that bring us the desired profit.
        # We pick the first of them, the one that brings us the best profit.
        opportunities = list(filter(lambda opportunity: opportunity.net_profit(investment_token) > self.minimum_profit, opportunities))
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
            print(f"  Executing {conversion.name()}")
            receipt = conversion.execute()
            if receipt is None:
                print(f"Execution failed")
                print(f"")
                print(f"Interrupting the process... Will start over from scratch in the next iteration.")
                return
            else:
                all_transfers += receipt.transfers
                outgoing = TransferFormatter().format(filter(Transfer.outgoing(self.our_address), receipt.transfers))
                incoming = TransferFormatter().format(filter(Transfer.incoming(self.our_address), receipt.transfers))
                print(f"  Execution successful, tx_hash={receipt.transaction_hash}")
                print(f"  Exchanged {outgoing} to {incoming}")

        print(f"")
        print(f"All steps executed successfully.")
        print(f"The profit we made is {TransferFormatter().format_net(all_transfers, self.our_address)}.")

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

        ERC20Token.register_token(self.tub.skr(), 'SKR')
        ERC20Token.register_token(self.tub.sai(), 'SAI')
        ERC20Token.register_token(self.tub.gem(), 'WETH')

        self.lpc_address = Address(config.get_contract_address("saiLpc"))
        self.lpc = Lpc(web3=web3, address=self.lpc_address)

        self.otc_address = Address(config.get_contract_address("otc"))
        self.otc = SimpleMarket(web3=web3, address=self.otc_address)

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
