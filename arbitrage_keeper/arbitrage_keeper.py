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
import sys
from typing import List

import os

import pkg_resources
from web3 import Web3, HTTPProvider

from keeper.conversion import Conversion
from keeper.conversion import OasisTakeConversion
from keeper.conversion import TubBoomConversion, TubBustConversion, TubExitConversion, TubJoinConversion
from keeper.opportunity import OpportunityFinder, Sequence
from keeper.transfer_formatter import TransferFormatter
from pymaker import Address, Contract
from pymaker.approval import via_tx_manager, directly
from pymaker.gas import DefaultGasPrice, FixedGasPrice
from pymaker.lifecycle import Web3Lifecycle
from pymaker.logger import Logger
from pymaker.numeric import Wad, Ray
from pymaker.oasis import MatchingMarket
from pymaker.sai import Tub, Tap
from pymaker.token import ERC20Token
from pymaker.transactional import TxManager
from pymaker.util import chain


class ArbitrageKeeper:
    """Keeper to arbitrage on OasisDEX, `join`, `exit`, `boom` and `bust`.

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

    The base token is the token all arbitrage opportunities will start with.
    Some amount of this token will be exchanged to some other token(s) and then exchanged
    back to the base token, aiming to end up with more of it than we started with.
    The keeper is aware of gas costs and takes a rough estimate of these costs while
    calculating arbitrage profitability.
    """

    def __init__(self, args, **kwargs):
        parser = argparse.ArgumentParser("arbitrage-keeper")

        parser.add_argument("--rpc-host", type=str, default="localhost",
                            help="JSON-RPC host (default: `localhost')")

        parser.add_argument("--rpc-port", type=int, default=8545,
                            help="JSON-RPC port (default: `8545')")

        parser.add_argument("--eth-from", type=str, required=True,
                            help="Ethereum account from which to send transactions")

        parser.add_argument("--tub-address", type=str, required=True,
                            help="Ethereum address of the Tub contract")

        parser.add_argument("--tap-address", type=str, required=True,
                            help="Ethereum address of the Tap contract")

        parser.add_argument("--oasis-address", type=str, required=True,
                            help="Ethereum address of the OasisDEX contract")

        parser.add_argument("--tx-manager", type=str,
                            help="Ethereum address of the TxManager contract to use for multi-step arbitrage")

        parser.add_argument("--gas-price", type=int, default=0,
                            help="Gas price in Wei (default: node default)")

        parser.add_argument("--base-token", type=str, required=True,
                            help="The token all arbitrage sequences will start and end with")

        parser.add_argument("--min-profit", type=float, required=True,
                            help="Minimum profit (in base token) from one arbitrage operation")

        parser.add_argument("--max-engagement", type=float, required=True,
                            help="Maximum engagement (in base token) in one arbitrage operation")

        parser.add_argument("--max-errors", type=int, default=100,
                            help="Maximum number of allowed errors before the keeper terminates (default: 100)")

        parser.add_argument("--debug", dest='debug', action='store_true',
                            help="Enable debug output")

        parser.add_argument("--trace", dest='trace', action='store_true',
                            help="Enable trace output")

        self.arguments = parser.parse_args(args)

        self.web3 = kwargs['web3'] if 'web3' in kwargs else Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))
        self.web3.eth.defaultAccount = self.arguments.eth_from

        self.chain = chain(self.web3)
        self.our_address = Address(self.arguments.eth_from)
        self.otc = MatchingMarket(web3=self.web3, address=Address(self.arguments.oasis_address))
        self.tub = Tub(web3=self.web3, address=Address(self.arguments.tub_address))
        self.tap = Tap(web3=self.web3, address=Address(self.arguments.tap_address))
        self.gem = ERC20Token(web3=self.web3, address=self.tub.gem())
        self.sai = ERC20Token(web3=self.web3, address=self.tub.sai())
        self.skr = ERC20Token(web3=self.web3, address=self.tub.skr())
        self.base_token = ERC20Token(web3=self.web3, address=Address(self.arguments.base_token))
        self.min_profit = Wad.from_number(self.arguments.min_profit)
        self.max_engagement = Wad.from_number(self.arguments.max_engagement)
        self.max_errors = self.arguments.max_errors
        self.errors = 0

        if self.arguments.tx_manager:
            self.tx_manager = TxManager(web3=self.web3, address=Address(self.arguments.tx_manager))
            if self.tx_manager.owner() != self.our_address:
                raise Exception(f"The TxManager has to be owned by the address the keeper is operating from.")
        else:
            self.tx_manager = None

        ERC20Token.register_token(self.tub.skr(), 'SKR')
        ERC20Token.register_token(self.tub.sai(), 'SAI')
        ERC20Token.register_token(self.tub.gem(), 'WETH')

        _json_log = os.path.abspath(pkg_resources.resource_filename(__name__, f"../logs/arbitrage-keeper_{self.chain}_{self.our_address}.json.log".lower()))
        self.logger = Logger('arbitrage-keeper', self.chain, _json_log, self.arguments.debug, self.arguments.trace)
        Contract.logger = self.logger

    def lifecycle(self):
        with Web3Lifecycle(self.web3, self.logger) as lifecycle:
            self.lifecycle = lifecycle
            lifecycle.on_startup(self.startup)

    def startup(self, lifecycle):
        self.approve()
        lifecycle.on_block(self.process_block)

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

    def otc_orders(self, tokens):
        return [order for order in self.otc.get_orders()
                if order.sell_which_token in tokens
                and order.buy_which_token in tokens]

    def otc_conversions(self, tokens) -> List[Conversion]:
        return list(map(lambda order: OasisTakeConversion(self.otc, order), self.otc_orders(tokens)))

    def all_conversions(self):
        return self.tub_conversions() + \
               self.otc_conversions([self.sai.address, self.skr.address, self.gem.address])

    def process_block(self):
        """Callback called on each new block.
        If too many errors, terminate the keeper to minimize potential damage."""
        if self.errors >= self.max_errors:
            self.lifecycle.terminate()
        else:
            self.execute_best_opportunity_available()

    def execute_best_opportunity_available(self):
        """Find the best arbitrage opportunity present and execute it."""
        opportunity = self.best_opportunity(self.profitable_opportunities())
        if opportunity:
            self.print_opportunity(opportunity)
            self.execute_opportunity(opportunity)

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

        def incoming_transfer(our_address: Address):
            return lambda transfer: transfer.to_address == our_address

        def outgoing_transfer(our_address: Address):
            return lambda transfer: transfer.from_address == our_address

        all_transfers = []
        for step in opportunity.steps:
            receipt = step.transact().transact(gas_price=self.gas_price())
            if receipt:
                all_transfers += receipt.transfers
                outgoing = TransferFormatter().format(filter(outgoing_transfer(self.our_address), receipt.transfers))
                incoming = TransferFormatter().format(filter(incoming_transfer(self.our_address), receipt.transfers))
                self.logger.info(f"Exchanged {outgoing} to {incoming}")
            else:
                self.errors += 1
                return
        self.logger.info(f"The profit we made is {TransferFormatter().format_net(all_transfers, self.our_address)}.")

    def execute_opportunity_in_one_transaction(self, opportunity: Sequence):
        """Execute the opportunity in one transaction, using the `tx_manager`."""
        tokens = [self.sai.address, self.skr.address, self.gem.address]
        invocations = list(map(lambda step: step.transact().invocation(), opportunity.steps))
        receipt = self.tx_manager.execute(tokens, invocations).transact(gas_price=self.gas_price())
        if receipt:
            self.logger.info(f"The profit we made is {TransferFormatter().format_net(receipt.transfers, self.our_address)}.")
        else:
            self.errors += 1

    def gas_price(self):
        if self.arguments.gas_price > 0:
            return FixedGasPrice(self.arguments.gas_price)
        else:
            return DefaultGasPrice()


if __name__ == '__main__':
    ArbitrageKeeper(sys.argv[1:]).lifecycle()
