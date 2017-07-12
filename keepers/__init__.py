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

import logging

import time

from web3 import Web3, HTTPProvider

from api import Address, register_filter_thread, all_filter_threads_alive, stop_all_filter_threads, \
    any_filter_thread_present
from api.token import ERC20Token


class Keeper:
    def __init__(self):
        logging_format = '%(asctime)-15s %(levelname)-8s %(name)-6s %(message)s'
        logging.basicConfig(format=logging_format, level=logging.INFO)
        parser = argparse.ArgumentParser(description=f"{type(self).__name__} keeper")
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
        self.args(parser)
        self.arguments = parser.parse_args()
        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))
        self.web3.eth.defaultAccount = self.arguments.eth_from #TODO allow to use ETH_FROM env variable
        self.our_address = Address(self.arguments.eth_from)
        self.config = Config(self.web3)

    def start(self):
        label = f"{type(self).__name__} keeper"
        logging.info(f"{label}")
        logging.info(f"{'-' * len(label)}")
        self._wait_for_init()
        logging.info(f"Keeper connected to {self.web3.currentProvider.endpoint_uri}")
        logging.info(f"Keeper operating as {self.our_address}")
        self._check_account_unlocked()
        logging.info("Keeper started")
        self.startup()

        while any_filter_thread_present():
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
            if not all_filter_threads_alive():
                logging.fatal("One of filter threads is dead, the keeper will terminate")
                break

        logging.info("Shutting down the keeper")
        if any_filter_thread_present():
            logging.info("Waiting for all threads to terminate...")
            stop_all_filter_threads()
        logging.info("Executing keeper shutdown logic...")
        self.shutdown()
        logging.info("Keeper terminated")

    def args(self, parser: argparse.ArgumentParser):
        pass

    def startup(self):
        raise NotImplementedError("Please implement the startup() method")

    def shutdown(self):
        pass

    def on_block(self, callback):
        def new_block_callback(block_hash):
            if not self.web3.eth.syncing:
                block = self.web3.eth.getBlock(block_hash)
                this_block_number = block['number']
                last_block_number = self.web3.eth.blockNumber
                if this_block_number == last_block_number:
                    logging.info(f"Processing block {block_hash}")
                    callback()
                else:
                    logging.info(f"Ignoring block {block_hash} (as #{this_block_number} < #{last_block_number})")
            else:
                logging.info(f"Ignoring block {block_hash} as the client is syncing")

        block_filter = self.web3.eth.filter('latest')
        block_filter.watch(new_block_callback)
        register_filter_thread(block_filter)

        logging.info("Watching for new blocks")

    def _wait_for_init(self):
        # wait for the client to have at least one peer
        if self.web3.net.peerCount == 0:
            logging.info(f"Waiting for the client to have at least one peer...")
            while self.web3.net.peerCount == 0:
                time.sleep(0.25)

        # wait for the client to sync completely,
        # as we do not want to apply keeper logic to stale blocks
        if self.web3.eth.syncing:
            logging.info(f"Waiting for the client to sync...")
            while self.web3.eth.syncing:
                time.sleep(0.25)

    def _check_account_unlocked(self):
        try:
            self.web3.eth.sign(self.web3.eth.defaultAccount, "test")
        except:
            logging.fatal(f"Account {self.web3.eth.defaultAccount} is not unlocked.")
            logging.fatal(f"Unlocking the account is necessary for the keeper to operate.")
            exit(-1)


class Config:
    def __init__(self, web3: Web3):
        with open('keepers/addresses.json') as data_file:
            self.network = self._network_name(web3)
            self.addresses = json.load(data_file)
        for key, value in self.addresses[self.network]["tokens"].items():
            ERC20Token.register_token(Address(value), key)

    def get_contract_address(self, name):
        return self.addresses[self.network]["contracts"].get(name, None)

    @staticmethod
    def _network_name(web3: Web3) -> str:
        block_0 = web3.eth.getBlock(0)['hash']
        if block_0 == "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3":
            block_1920000 = web3.eth.getBlock(1920000)['hash']
            if block_1920000 == "0x94365e3a8c0b35089c1d1195081fe7489b528a84b22199c916180db8b28ade7f":
                return "etclive"
            else:
                return "ethlive"
        elif block_0 == "0xa3c565fc15c7478862d50ccd6561e3c06b24cc509bf388941c25ea985ce32cb9":
            return "kovan"
        elif block_0 == "0x41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d":
            return "ropsten"
        elif block_0 == "0x0cd786a2425d16f152c658316c423e6ce1181e15c3295826d7c9904cba9ce303":
            return "morden"
        else:
            return "unknown"
