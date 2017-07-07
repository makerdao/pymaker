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

import logging

import time

import sys
from web3 import Web3

from api import register_filter_thread, all_filter_threads_alive


def for_each_block(web3: Web3, func):
    def new_block_callback(block_hash):
        if not web3.eth.syncing:
            block = web3.eth.getBlock(block_hash)
            this_block_number = block['number']
            last_block_number = web3.eth.blockNumber
            if this_block_number == last_block_number:
                logging.debug(f"Processing block {block_hash}")
                func()
            else:
                logging.info(f"Ignoring block {block_hash} as #{this_block_number} < #{last_block_number}")
        else:
            logging.info(f"Ignoring block {block_hash} as the client is syncing")

    # wait for the client to have at least one peer
    if web3.net.peerCount == 0:
        logging.info(f"Waiting for the client to have at least one peer...")
        while web3.net.peerCount == 0:
            time.sleep(0.25)

    # wait for the client to sync completely,
    # as we do not want to apply keeper logic to stale blocks
    if web3.eth.syncing:
        logging.info(f"Waiting for the client to sync...")
        while web3.eth.syncing:
            time.sleep(0.25)

    # watch for new blocks
    logging.info("Watching for new blocks...")
    block_filter = web3.eth.filter('latest')
    block_filter.watch(new_block_callback)
    register_filter_thread(block_filter)
    while True:
        if not all_filter_threads_alive():
            logging.fatal("One of filter threads is dead. Shutting down the keeper.")
            sys.exit(-1)
        time.sleep(1)


def check_account_unlocked(web3: Web3):
    try:
        web3.eth.sign(web3.eth.defaultAccount, "test")
    except:
        logging.fatal(f"Account {web3.eth.defaultAccount} is not unlocked.")
        logging.fatal(f"Unlocking the account is necessary for the keeper to operate.")
        exit(-1)
