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
import time
from typing import List

from api import Address, Transfer
from api.numeric import Ray
from api.numeric import Wad
from api.otc import SimpleMarket
from api.sai import Tub, Lpc
from api.token import ERC20Token
from api.transact import Invocation, TxManager
from keepers import Keeper
from keepers.arbitrage.conversion import Conversion
from keepers.arbitrage.conversion import LpcTakeAltConversion, LpcTakeRefConversion
from keepers.arbitrage.conversion import OasisTakeConversion
from keepers.arbitrage.conversion import TubBoomConversion, TubBustConversion, TubExitConversion, TubJoinConversion
from keepers.arbitrage.opportunity import OpportunityFinder
from keepers.arbitrage.transfer_formatter import TransferFormatter


class SaiArbitrage(Keeper):
    def args(self, parser: argparse.ArgumentParser):
        parser.add_argument("--frequency", help="Monitoring frequency in seconds (default: 5)", default=5, type=float)
        parser.add_argument("--minimum-profit", help="Minimum profit in SAI from one arbitrage operation (default: 0.01)", default=0.01, type=float)
        parser.add_argument("--maximum-engagement", help="Maximum engagement in SAI in one arbitrage operation (default: 1000)", default=1000, type=float)
        parser.add_argument("--tx-manager", help="Address of the TxManager to use for multi-step arbitrage", type=str)

    def init(self):
        self.tub_address = Address(self.config.get_contract_address("saiTub"))
        self.tap_address = Address(self.config.get_contract_address("saiTap"))
        self.top_address = Address(self.config.get_contract_address("saiTop"))
        self.tub = Tub(web3=self.web3, address_tub=self.tub_address, address_tap=self.tap_address, address_top=self.top_address)
        self.lpc_address = Address(self.config.get_contract_address("saiLpc"))
        self.lpc = Lpc(web3=self.web3, address=self.lpc_address)
        self.otc_address = Address(self.config.get_contract_address("otc"))
        self.otc = SimpleMarket(web3=self.web3, address=self.otc_address)

        self.skr = ERC20Token(web3=self.web3, address=self.tub.skr())
        self.sai = ERC20Token(web3=self.web3, address=self.tub.sai())
        self.gem = ERC20Token(web3=self.web3, address=self.tub.gem())
        ERC20Token.register_token(self.tub.skr(), 'SKR')
        ERC20Token.register_token(self.tub.sai(), 'SAI')
        ERC20Token.register_token(self.tub.gem(), 'WETH')

        self.base_token = self.sai
        self.minimum_profit = Wad.from_number(self.arguments.minimum_profit)
        self.maximum_engagement = Wad.from_number(self.arguments.maximum_engagement)

        if self.arguments.tx_manager:
            self.tx_manager_address = Address(self.arguments.tx_manager)
            self.tx_manager = TxManager(web3=self.web3, address=self.tx_manager_address)
            if self.tx_manager.owner() != self.our_address:
                print(f"The TxManager has to be owned by the address the keeper is operating from.")
                exit(-1)
        else:
            self.tx_manager_address = None
            self.tx_manager = None

    def run(self):
        self.setup_allowances()
        self.print_balances()
        while True:
            self.execute_best_opportunity_available()
            time.sleep(self.arguments.frequency)

    def print_balances(self):
        def balances():
            for token in [self.sai, self.skr, self.gem]:
                yield f"{token.balance_of(self.our_address)} {token.name()}"
        print(f"Keeper balances are {', '.join(balances())}.")

    def setup_allowances(self):
        """Approve all components that need to access our balances"""
        self.setup_tub_allowances()
        self.setup_lpc_allowances()
        self.setup_otc_allowances()
        self.setup_tx_manager_allowances()

    def setup_tub_allowances(self):
        """Approve Tub components so we can call join()/exit() and boom()/bust()"""
        self.setup_allowance(self.gem, self.tub.jar(), 'Tub.jar')
        self.setup_allowance(self.skr, self.tub.jar(), 'Tub.jar')
        self.setup_allowance(self.skr, self.tub.pit(), 'Tub.pit')
        self.setup_allowance(self.sai, self.tub.pit(), 'Tub.pit')

    def setup_lpc_allowances(self):
        """Approve the Lpc so we can exchange WETH and SAI using it"""
        self.setup_allowance(self.gem, self.lpc.address, 'Lpc')
        self.setup_allowance(self.sai, self.lpc.address, 'Lpc')

    def setup_otc_allowances(self):
        """Approve OasisDEX so we can exchange all three tokens (WETH, SAI and SKR)"""
        self.setup_allowance(self.gem, self.otc.address, 'OasisDEX')
        self.setup_allowance(self.sai, self.otc.address, 'OasisDEX')
        self.setup_allowance(self.skr, self.otc.address, 'OasisDEX')

    def setup_tx_manager_allowances(self):
        """Approve the `TxManager` so it can pull all three tokens (WETH, SAI and SKR) from us"""
        if self.tx_manager:
            self.setup_allowance(self.gem, self.tx_manager.address, 'TxManager')
            self.setup_allowance(self.sai, self.tx_manager.address, 'TxManager')
            self.setup_allowance(self.skr, self.tx_manager.address, 'TxManager')

    def setup_allowance(self, token: ERC20Token, spender_address: Address, spender_name: str):
        #TODO actually only one of these paths is needed, depending on whether we are using a
        #TxManager or not
        if token.allowance_of(self.our_address, spender_address) < Wad(2 ** 128 - 1):
            print(f"Approving {spender_name} ({spender_address}) to access our {token.name()} balance directly...")
            if not token.approve(spender_address):
                print(f"Approval failed!")
                exit(-1)

        if self.tx_manager and spender_address != self.tx_manager.address and \
                        token.allowance_of(self.tx_manager.address, spender_address) < Wad(2 ** 128 - 1):
            print(f"Approving {spender_name} ({spender_address}) to access our {token.name()} balance indirectly...")
            invocation = Invocation(address=token.address, calldata=token.approve_calldata(spender_address))
            if not self.tx_manager.execute([], [invocation]):
                print(f"Approval failed!")
                exit(-1)

    def tub_conversions(self) -> List[Conversion]:
        return [TubJoinConversion(self.tub),
                TubExitConversion(self.tub),
                TubBoomConversion(self.tub),
                TubBustConversion(self.tub)]

    def lpc_conversions(self) -> List[Conversion]:
        return [LpcTakeRefConversion(self.lpc),
                LpcTakeAltConversion(self.lpc)]

    def otc_offers(self, tokens):
        offers = [self.otc.get_offer(offer_id + 1) for offer_id in range(self.otc.get_last_offer_id())]
        offers = [offer for offer in offers if offer is not None]
        return [offer for offer in offers if offer.sell_which_token in tokens and offer.buy_which_token in tokens]

    def otc_conversions(self, tokens) -> List[Conversion]:
        return list(map(lambda offer: OasisTakeConversion(self.otc, offer), self.otc_offers(tokens)))

    def all_conversions(self):
        return self.tub_conversions() + self.lpc_conversions() + \
               self.otc_conversions([self.sai.address, self.skr.address, self.gem.address])

    def execute_best_opportunity_available(self):
        """Find the best arbitrage opportunity present and execute it."""
        opportunity = self.best_opportunity(self.profitable_opportunities())
        if opportunity:
            self.print_opportunity(opportunity)
            self.execute_opportunity(opportunity)

    def profitable_opportunities(self):
        """Identify all profitable arbitrage opportunities within given limits."""
        entry_amount = Wad.min(self.base_token.balance_of(self.our_address), self.maximum_engagement)
        opportunity_finder = OpportunityFinder(conversions=self.all_conversions())
        opportunities = opportunity_finder.find_opportunities(self.base_token.address, entry_amount)
        opportunities = filter(lambda op: op.total_rate() > Ray.from_number(1.000001), opportunities)
        opportunities = filter(lambda op: op.net_profit(self.base_token.address) > self.minimum_profit, opportunities)
        opportunities = sorted(opportunities, key=lambda op: op.net_profit(self.base_token.address), reverse=True)
        return opportunities

    def best_opportunity(self, opportunities):
        """Pick the best opportunity, or return None if no profitable opportunities."""
        return opportunities[0] if len(opportunities) > 0 else None

    def print_opportunity(self, opportunity):
        """Print the details of the opportunity."""
        print(f"")
        print(f"Opportunity with profit={opportunity.net_profit(self.base_token.address)} {self.base_token.name()} "
              f"net_profit={opportunity.net_profit(self.base_token.address)} {self.base_token.name()}")
        for index, conversion in enumerate(opportunity.conversions, start=1):
            print(f"Step {index}/{len(opportunity.conversions)}:")
            print(f"  Exchange {conversion.source_amount} {ERC20Token.token_name_by_address(conversion.source_token)} "
                  f"to {conversion.target_amount} {ERC20Token.token_name_by_address(conversion.target_token)}")
            print(f"  Using {conversion.name()}")

    def execute_opportunity(self, opportunity):
        """Execute the opportunity either in one Ethereum transaction or step-by-step.
        Depending on whether `tx_manager` is available."""
        if self.tx_manager:
            self.execute_opportunity_in_one_transaction(opportunity)
        else:
            self.execute_opportunity_step_by_step(opportunity)

    def execute_opportunity_step_by_step(self, opportunity):
        """Execute the opportunity step-by-step."""
        all_transfers = []
        for index, conversion in enumerate(opportunity.conversions, start=1):
            print(f"Executing step {index}/{len(opportunity.conversions)}... ", end='', flush=True)
            receipt = conversion.execute()
            if receipt is None:
                print(f"FAILED!")
                print(f"")
                print(f"Interrupting the process... Will start over from scratch in the next iteration.")
                return
            else:
                print(f"ok (tx_hash={receipt.transaction_hash})")
                all_transfers += receipt.transfers
                outgoing = TransferFormatter().format(filter(Transfer.outgoing(self.our_address), receipt.transfers))
                incoming = TransferFormatter().format(filter(Transfer.incoming(self.our_address), receipt.transfers))
                print(f"  Exchanged {outgoing} to {incoming}")
        print(f"All steps executed successfully.")
        print(f"The profit we made is {TransferFormatter().format_net(all_transfers, self.our_address)}.")
        self.print_balances()

    def execute_opportunity_in_one_transaction(self, opportunity):
        """Execute the opportunity in one transaction, using the `tx_manager`."""
        print(f"Executing all steps in one transaction... ", end='', flush=True)

        invocations = list(map(lambda conv: Invocation(conv.address(), conv.calldata()), opportunity.conversions))
        receipt = self.tx_manager.execute([self.sai.address, self.skr.address, self.gem.address], invocations)
        if receipt:
            print(f"ok (tx_hash={receipt.transaction_hash})")
            print(f"The profit we made is {TransferFormatter().format_net(receipt.transfers, self.our_address)}.")
        else:
            print(f"FAILED!")
            exit(-1) #TODO while we debug


if __name__ == '__main__':
    SaiArbitrage().start()
