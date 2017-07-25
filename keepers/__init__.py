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
import threading

import time

import datetime
from web3 import Web3, HTTPProvider

from api import Address, register_filter_thread, all_filter_threads_alive, stop_all_filter_threads, \
    any_filter_thread_present, Wad
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
        self.config = Config(self.chain())
        self.terminated = False
        self._last_block_time = None

    def start(self):
        label = f"{type(self).__name__} keeper"
        logging.info(f"{label}")
        logging.info(f"{'-' * len(label)}")
        self._wait_for_init()
        logging.info(f"Keeper on {self.chain()}, connected to {self.web3.currentProvider.endpoint_uri}")
        logging.info(f"Keeper operating as {self.our_address}")
        self._check_account_unlocked()
        logging.info("Keeper started")
        self.startup()
        self._main_loop()
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
    
    def terminate(self):
        self.terminated = True

    def chain(self) -> str:
        block_0 = self.web3.eth.getBlock(0)['hash']
        if block_0 == "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3":
            block_1920000 = self.web3.eth.getBlock(1920000)['hash']
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

    def eth_balance(self, address: Address) -> Wad:
        assert(isinstance(address, Address))
        return Wad(self.web3.eth.getBalance(address.address))

    def on_block(self, callback):
        def new_block_callback(block_hash):
            self._last_block_time = datetime.datetime.now()
            if True: #TODO syncing check broken after web3.py upgrade to 3.10.0 -- if not self.web3.eth.syncing:
                block = self.web3.eth.getBlock(block_hash)
                this_block_number = block['number']
                last_block_number = self.web3.eth.blockNumber
                if this_block_number == last_block_number:
                    logging.debug(f"Processing block {block_hash}")
                    callback()
                else:
                    logging.info(f"Ignoring block {block_hash} (as #{this_block_number} < #{last_block_number})")
            else:
                logging.info(f"Ignoring block {block_hash} as the client is syncing")

        block_filter = self.web3.eth.filter('latest')
        block_filter.watch(new_block_callback)
        register_filter_thread(block_filter)

        logging.info("Watching for new blocks")

    def every(self, time_in_seconds, callback):
        def func():
            callback()
            timer = threading.Timer(time_in_seconds, func)
            timer.daemon = True
            timer.start()
        func()

    def _wait_for_init(self):
        # wait for the client to have at least one peer
        if self.web3.net.peerCount == 0:
            logging.info(f"Waiting for the client to have at least one peer...")
            while self.web3.net.peerCount == 0:
                time.sleep(0.25)

        #TODO syncing check broken after web3.py upgrade to 3.10.0
        #TODO uncomment section below when fixed
        # wait for the client to sync completely,
        # as we do not want to apply keeper logic to stale blocks
        # if self.web3.eth.syncing:
        #     logging.info(f"Waiting for the client to sync...")
        #     while self.web3.eth.syncing:
        #         time.sleep(0.25)

    def _check_account_unlocked(self):
        try:
            self.web3.eth.sign(self.web3.eth.defaultAccount, "test")
        except:
            logging.fatal(f"Account {self.web3.eth.defaultAccount} is not unlocked.")
            logging.fatal(f"Unlocking the account is necessary for the keeper to operate.")
            exit(-1)

    def _main_loop(self):
        # in case at least one filter has been set up, we enter an infinite loop and let
        # the callbacks do the job. in case of no filters, we will not enter this loop
        # and the keeper will terminate soon after it started
        while any_filter_thread_present():
            # we watch for KeyboardInterrupt in order to detect SIGINT signals
            # capturing this event allows the keeper to shutdown gracefully
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

            # if the keeper logic asked us to terminate, we do so
            if self.terminated:
                logging.warning("Keeper logic asked for termination, the keeper will terminate")
                break

            # if any exception is raised in filter handling thread (could be an HTTP exception
            # while communicating with the node), web3.py does not retry and the filter becomes
            # dysfunctional i.e. no new callbacks will ever be fired. we detect it and terminate
            # the keeper so it can be restarted.
            if not all_filter_threads_alive():
                logging.fatal("One of filter threads is dead, the keeper will terminate")
                break

            # if we are watching for new blocks and no new block has been reported during
            # the last 2 minutes, we assume the watching filter died and terminate the keeper
            # so it can be restarted.
            #
            # this used to happen when the machine that has the node and the keeper running
            # was put to sleep and then woken up.
            #
            # TODO the same thing could possibly happen if we watch any event other than
            # TODO a new block. if that happens, we have no reliable way of detecting it now.
            if self._last_block_time and (datetime.datetime.now() - self._last_block_time).total_seconds() > 300:
                if True: #TODO syncing check broken after web3.py upgrade to 3.10.0 if not self.web3.eth.syncing:
                    logging.fatal("No new blocks received for 300 seconds, the keeper will terminate")
                    break


class Config:
    def __init__(self, chain: str):
        with open('keepers/config.json') as data_file:
            self.chain = chain
            self.config = json.load(data_file)
        for key, value in self.config[self.chain]["tokens"].items():
            ERC20Token.register_token(Address(value), key)

    def get_config(self):
        return self.config[self.chain]

    def get_contract_address(self, name):
        return self.config[self.chain]["contracts"].get(name, None)

