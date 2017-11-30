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
import json
import os
import sys

import pkg_resources

from keeper.api import Address, register_filter_thread, all_filter_threads_alive, stop_all_filter_threads, \
    any_filter_thread_present, Wad, Contract
from keeper.api.gas import FixedGasPrice, DefaultGasPrice, GasPrice
from keeper.api.logger import Logger, Event
from keeper.api.util import AsyncCallback, chain
from web3 import Web3, HTTPProvider

from keeper.api.token import ERC20Token
from keeper.lifecycle import Web3Lifecycle


class Keeper:
    def __init__(self, args: list, **kwargs):
        parser = argparse.ArgumentParser(prog=self.executable_name())
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
        parser.add_argument("--gas-price", help="Static gas pricing: Gas price in Wei", default=0, type=int)
        parser.add_argument("--debug", help="Enable debug output", dest='debug', action='store_true')
        parser.add_argument("--trace", help="Enable trace output", dest='trace', action='store_true')
        self.args(parser)
        self.arguments = parser.parse_args(args)
        self.web3 = kwargs['web3'] if 'web3' in kwargs else Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))
        self.web3.eth.defaultAccount = self.arguments.eth_from
        self.our_address = Address(self.arguments.eth_from)
        self.chain = chain(self.web3)
        self.config = kwargs['config'] if 'config' in kwargs else Config.load_config(self.chain)
        self.gas_price = self._get_gas_price()
        self.terminated_internally = False
        self.terminated_externally = False
        self.fatal_termination = False
        self._at_least_one_every = False
        self._last_block_time = None
        self._on_block_callback = None
        self._config_checksum = {}
        _json_log = os.path.abspath(pkg_resources.resource_filename(__name__, f"../logs/{self.executable_name()}_{self.chain}_{self.our_address}.json.log".lower()))
        self.logger = Logger(self.keeper_name(), self.chain, _json_log, self.arguments.debug, self.arguments.trace)
        Contract.logger = self.logger

    def start(self):
        with Web3Lifecycle(self.web3, self.logger) as lifecycle:
            self.lifecycle = lifecycle
            lifecycle.on_startup(lambda lifecycle: self.startup())
            lifecycle.on_shutdown(lambda lifecycle: self.shutdown())

    def args(self, parser: argparse.ArgumentParser):
        pass

    def startup(self):
        raise NotImplementedError("Please implement the startup() method")

    def shutdown(self):
        pass
    
    def terminate(self, message=None):
        self.lifecycle.terminate(message)

    @staticmethod
    def keeper_name():
        return os.path.basename(sys.argv[0]).replace('_', '-').replace('.py', '')

    def executable_name(self):
        return "keeper-" + self.keeper_name()

    def eth_balance(self, address: Address) -> Wad:
        assert(isinstance(address, Address))
        return Wad(self.web3.eth.getBalance(address.address))

    # def print_eth_balance(self):
    #     balance = self.eth_balance(self.our_address)
    #     self.logger.info(f"Keeper account balance is {balance} ETH", Event.eth_balance(self.our_address, balance))

    def on_block(self, callback):
        self.lifecycle.on_block(callback)

    def every(self, frequency_in_seconds: int, callback):
        self.lifecycle.every(frequency_in_seconds, callback)

    def _get_gas_price(self) -> GasPrice:
        if self.arguments.gas_price > 0:
            return FixedGasPrice(self.arguments.gas_price)
        else:
            return DefaultGasPrice()


class Config:
    def __init__(self, config: dict):
        self.config = config

    @classmethod
    def load_config(cls, chain: str):
        with open('keeper/config.json') as data_file:
            return Config(json.load(data_file)[chain])

    def get_config(self):
        return self.config

    def get_contract_address(self, name):
        return self.config["contracts"].get(name, None)
