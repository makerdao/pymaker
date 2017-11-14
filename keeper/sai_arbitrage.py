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
from typing import List

import sys

from keeper.api import Address, Transfer
from keeper.api.approval import via_tx_manager, directly
from keeper.api.numeric import Ray
from keeper.api.numeric import Wad
from keeper.api.transact import Invocation, TxManager

from keeper.api.token import ERC20Token
from keeper.conversion import Conversion
from keeper.conversion import OasisTakeConversion
from keeper.conversion import TubBoomConversion, TubBustConversion, TubExitConversion, TubJoinConversion
from keeper.opportunity import OpportunityFinder, Sequence
from keeper.sai import SaiKeeper
from keeper.transfer_formatter import TransferFormatter


class SaiArbitrage(SaiKeeper):
    """SAI keeper to arbitrage on OasisDEX, `join`, `exit`, `boom` and `bust`.

    Keeper constantly looks for profitable enough arbitrage opportunities
    and executes them the moment they become available. It can make profit on:
    - taking orders on OasisDEX (on SAI/SKR, SAI/W-ETH and SKR/W-ETH pairs),
    - calling `join` and `exit` to exchange between W-ETH and SKR,
    - calling `boom` and `bust` to exchange between SAI and SKR.

    Opportunities discovered by the keeper are sequences of token exchanges
    executed using methods listed above. An opportunity can consist of two
    or three steps, technically it could be more but practically it will never
    be more than three.

    Steps can be executed sequentially (each one as a separate Etheruem
    transaction, checking if one has been successful before executing the next
    one) or in one ago. The latter method requires a `TxManager` contract deployed,
    its address has to be passed as the `--tx-manager` argument. Also the `TxManager`
    contract has to be owned by the account the keeper operates from.

    You can find the source code of the `TxManager` here:
    <https://github.com/reverendus/tx-manager>.

    The base token of this keeper is SAI i.e. all arbitrage opportunities will
    start with some amount of SAI, exchange it to some other token(s) and then exchange
    back to SAI, aiming to end up with more SAI than it started with. The keeper is aware
    of gas costs and takes a rough estimate of these costs while calculating arbitrage
    profitability.
    """

    def __init__(self, args, **kwargs):
        super().__init__(args, **kwargs)
        self.base_token = ERC20Token(web3=self.web3,
                                     address=ERC20Token.token_address_by_name(self.arguments.base_token))
        self.min_profit = Wad.from_number(self.arguments.min_profit)
        self.max_engagement = Wad.from_number(self.arguments.max_engagement)
        self.max_errors = self.arguments.max_errors
        self.errors = 0

        if self.arguments.tx_manager:
            self.tx_manager_address = Address(self.arguments.tx_manager)
            self.tx_manager = TxManager(web3=self.web3, address=self.tx_manager_address)
            if self.tx_manager.owner() != self.our_address:
                self.logger.info(f"The TxManager has to be owned by the address the keeper is operating from.")
                exit(-1)
        else:
            self.tx_manager_address = None
            self.tx_manager = None

    def args(self, parser: argparse.ArgumentParser):
        parser.add_argument("--base-token", type=str, required=True,
                            help="The token all arbitrage sequences will start and end with")

        parser.add_argument("--min-profit", type=float, required=True,
                            help="Minimum profit (in base token) from one arbitrage operation")

        parser.add_argument("--max-engagement", type=float, required=True,
                            help="Maximum engagement (in base token) in one arbitrage operation")

        parser.add_argument("--max-errors", type=int, default=100,
                            help="Maximum number of allowed errors before the keeper terminates (default: 100)")

        parser.add_argument("--tx-manager", type=str,
                            help="Address of the TxManager to use for multi-step arbitrage")

    def startup(self):
        self.approve()
        self.on_block(self.process_block)
        self.every(60*60, self.print_balances)

    def print_balances(self):
        def balances():
            for token in [self.sai, self.skr, self.gem]:
                yield f"{token.balance_of(self.our_address)} {token.name()}"
        self.logger.info(f"Keeper balances are {', '.join(balances())}.")

    def approve(self):
        """Approve all components that need to access our balances"""
        approval_method = via_tx_manager(self.tx_manager) if self.tx_manager else directly()
        self.tub.approve(approval_method)
        self.otc.approve([self.gem, self.sai, self.skr], approval_method)
        if self.tx_manager:
            self.tx_manager.approve([self.gem, self.sai, self.skr], directly())

    def tub_conversions(self) -> List[Conversion]:
        return [TubJoinConversion(self.tub),
                TubExitConversion(self.tub),
                TubBoomConversion(self.tub, self.tap),
                TubBustConversion(self.tub, self.tap)]

    def otc_offers(self, tokens):
        return [offer for offer in self.otc.active_offers()
                if offer.sell_which_token in tokens
                and offer.buy_which_token in tokens]

    def otc_conversions(self, tokens) -> List[Conversion]:
        return list(map(lambda offer: OasisTakeConversion(self.otc, offer), self.otc_offers(tokens)))

    def all_conversions(self):
        return self.tub_conversions() + \
               self.otc_conversions([self.sai.address, self.skr.address, self.gem.address])

    def process_block(self):
        """Callback called on each new block.
        If too many errors, terminate the keeper to minimize potential damage."""
        if self.errors >= self.max_errors:
            self.terminate()
        else:
            self.execute_best_opportunity_available()

    def execute_best_opportunity_available(self):
        """Find the best arbitrage opportunity present and execute it."""
        opportunity = self.best_opportunity(self.profitable_opportunities())
        if opportunity:
            self.print_opportunity(opportunity)
            self.execute_opportunity(opportunity)
            self.print_balances()

    def profitable_opportunities(self):
        """Identify all profitable arbitrage opportunities within given limits."""
        entry_amount = Wad.min(self.base_token.balance_of(self.our_address), self.max_engagement)
        opportunity_finder = OpportunityFinder(conversions=self.all_conversions())
        opportunities = opportunity_finder.find_opportunities(self.base_token.address, entry_amount)
        opportunities = filter(lambda op: op.total_rate() > Ray.from_number(1.000001), opportunities)
        opportunities = filter(lambda op: op.net_profit(self.base_token.address) > self.min_profit, opportunities)
        opportunities = sorted(opportunities, key=lambda op: op.net_profit(self.base_token.address), reverse=True)
        return opportunities

    def best_opportunity(self, opportunities: List[Sequence]):
        """Pick the best opportunity, or return None if no profitable opportunities."""
        return opportunities[0] if len(opportunities) > 0 else None

    def print_opportunity(self, opportunity: Sequence):
        """Print the details of the opportunity."""
        self.logger.info(f"Opportunity with profit={opportunity.profit(self.base_token.address)} {self.base_token.name()},"
                         f" net_profit={opportunity.net_profit(self.base_token.address)} {self.base_token.name()}")
        for index, conversion in enumerate(opportunity.steps, start=1):
            self.logger.info(f"Step {index}/{len(opportunity.steps)}:"
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
        for step in opportunity.steps:
            receipt = step.transact().transact(gas_price=self.gas_price)
            if receipt:
                all_transfers += receipt.transfers
                outgoing = TransferFormatter().format(filter(Transfer.outgoing(self.our_address), receipt.transfers))
                incoming = TransferFormatter().format(filter(Transfer.incoming(self.our_address), receipt.transfers))
                self.logger.info(f"Exchanged {outgoing} to {incoming}")
            else:
                self.errors += 1
                return
        self.logger.info(f"The profit we made is {TransferFormatter().format_net(all_transfers, self.our_address)}.")

    def execute_opportunity_in_one_transaction(self, opportunity: Sequence):
        """Execute the opportunity in one transaction, using the `tx_manager`."""
        tokens = [self.sai.address, self.skr.address, self.gem.address]
        invocations = list(map(lambda step: step.transact().invocation(), opportunity.steps))
        receipt = self.tx_manager.execute(tokens, invocations).transact(gas_price=self.gas_price)
        if receipt:
            self.logger.info(f"The profit we made is {TransferFormatter().format_net(receipt.transfers, self.our_address)}.")
        else:
            self.errors += 1


if __name__ == '__main__':
    SaiArbitrage(sys.argv[1:]).start()
