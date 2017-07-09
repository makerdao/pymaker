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
import logging
from typing import List

from api import Address, Transfer
from api.approval import via_tx_manager, directly
from api.numeric import Ray
from api.numeric import Wad
from api.token import ERC20Token
from api.transact import Invocation, TxManager
from keepers.arbitrage.conversion import Conversion
from keepers.arbitrage.conversion import LpcTakeAltConversion, LpcTakeRefConversion
from keepers.arbitrage.conversion import OasisTakeConversion
from keepers.arbitrage.conversion import TubBoomConversion, TubBustConversion, TubExitConversion, TubJoinConversion
from keepers.arbitrage.opportunity import OpportunityFinder, Sequence
from keepers.arbitrage.transfer_formatter import TransferFormatter
from keepers.sai import SaiKeeper


class SaiArbitrage(SaiKeeper):
    def __init__(self):
        super().__init__()
        self.base_token = self.sai
        self.minimum_profit = Wad.from_number(self.arguments.minimum_profit)
        self.maximum_engagement = Wad.from_number(self.arguments.maximum_engagement)

        if self.arguments.tx_manager:
            self.tx_manager_address = Address(self.arguments.tx_manager)
            self.tx_manager = TxManager(web3=self.web3, address=self.tx_manager_address)
            if self.tx_manager.owner() != self.our_address:
                logging.info(f"The TxManager has to be owned by the address the keeper is operating from.")
                exit(-1)
        else:
            self.tx_manager_address = None
            self.tx_manager = None

    def args(self, parser: argparse.ArgumentParser):
        parser.add_argument("--minimum-profit", help="Minimum profit in SAI from one arbitrage operation (default: 0.01)", default=0.01, type=float)
        parser.add_argument("--maximum-engagement", help="Maximum engagement in SAI in one arbitrage operation (default: 1000)", default=1000, type=float)
        parser.add_argument("--tx-manager", help="Address of the TxManager to use for multi-step arbitrage", type=str)

    def startup(self):
        self.approve()
        self.print_balances()
        self.on_block(self.execute_best_opportunity_available)

    def print_balances(self):
        def balances():
            for token in [self.sai, self.skr, self.gem]:
                yield f"{token.balance_of(self.our_address)} {token.name()}"
        logging.info(f"Keeper balances are {', '.join(balances())}.")

    def approve(self):
        """Approve all components that need to access our balances"""
        approval_method = via_tx_manager(self.tx_manager) if self.tx_manager else directly()
        self.lpc.approve(approval_method)
        self.tub.approve(approval_method)
        self.otc.approve([self.gem, self.sai, self.skr], approval_method)
        if self.tx_manager:
            self.tx_manager.approve([self.gem, self.sai, self.skr], directly())

    def tub_conversions(self) -> List[Conversion]:
        return [TubJoinConversion(self.tub),
                TubExitConversion(self.tub),
                TubBoomConversion(self.tub),
                TubBustConversion(self.tub)]

    def lpc_conversions(self) -> List[Conversion]:
        return [LpcTakeRefConversion(self.lpc),
                LpcTakeAltConversion(self.lpc)]

    def otc_offers(self, tokens):
        return [offer for offer in self.otc.active_offers()
                if offer.sell_which_token in tokens and offer.buy_which_token in tokens]

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
            self.print_balances()

    def profitable_opportunities(self):
        """Identify all profitable arbitrage opportunities within given limits."""
        entry_amount = Wad.min(self.base_token.balance_of(self.our_address), self.maximum_engagement)
        opportunity_finder = OpportunityFinder(conversions=self.all_conversions())
        opportunities = opportunity_finder.find_opportunities(self.base_token.address, entry_amount)
        opportunities = filter(lambda op: op.total_rate() > Ray.from_number(1.000001), opportunities)
        opportunities = filter(lambda op: op.net_profit(self.base_token.address) > self.minimum_profit, opportunities)
        opportunities = sorted(opportunities, key=lambda op: op.net_profit(self.base_token.address), reverse=True)
        return opportunities

    def best_opportunity(self, opportunities: List[Sequence]):
        """Pick the best opportunity, or return None if no profitable opportunities."""
        return opportunities[0] if len(opportunities) > 0 else None

    def print_opportunity(self, opportunity: Sequence):
        """Print the details of the opportunity."""
        logging.info(f"Opportunity with profit={opportunity.profit(self.base_token.address)} {self.base_token.name()},"
                     f" net_profit={opportunity.net_profit(self.base_token.address)} {self.base_token.name()}")
        for index, conversion in enumerate(opportunity.steps, start=1):
            logging.info(f"Step {index}/{len(opportunity.steps)}:"
                         f" from {conversion.source_amount} {ERC20Token.token_name_by_address(conversion.source_token)}"
                         f" to {conversion.target_amount} {ERC20Token.token_name_by_address(conversion.target_token)}"
                         f" using {conversion.name()}")

    def execute_opportunity(self, opportunity: Sequence):
        """Execute the opportunity either in one Ethereum transaction or step-by-step.
        Depending on whether `tx_manager` is available."""
        if self.tx_manager:
            self.execute_opportunity_in_one_transaction(opportunity)
        else:
            self.execute_opportunity_step_by_step(opportunity)

    def execute_opportunity_step_by_step(self, opportunity: Sequence):
        """Execute the opportunity step-by-step."""
        all_transfers = []
        for conversion in opportunity.steps:
            receipt = conversion.execute()
            if receipt:
                all_transfers += receipt.transfers
                outgoing = TransferFormatter().format(filter(Transfer.outgoing(self.our_address), receipt.transfers))
                incoming = TransferFormatter().format(filter(Transfer.incoming(self.our_address), receipt.transfers))
                logging.info(f"Exchanged {outgoing} to {incoming}")
            else:
                return
        logging.info(f"The profit we made is {TransferFormatter().format_net(all_transfers, self.our_address)}.")

    def execute_opportunity_in_one_transaction(self, opportunity: Sequence):
        """Execute the opportunity in one transaction, using the `tx_manager`."""
        invocations = list(map(lambda conv: Invocation(conv.address(), conv.calldata()), opportunity.steps))
        receipt = self.tx_manager.execute([self.sai.address, self.skr.address, self.gem.address], invocations)
        if receipt:
            logging.info(f"The profit we made is {TransferFormatter().format_net(receipt.transfers, self.our_address)}.")
        else:
            exit(-1) #TODO while we debug


if __name__ == '__main__':
    SaiArbitrage().start()
