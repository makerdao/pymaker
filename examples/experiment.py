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
import sys

import time

import logging
from web3 import HTTPProvider
from web3 import Web3

from api import Address, Calldata
from api.token import ERC20Token
from api.sai import Tub
from api.transact import TxManager, Invocation
from keepers.monitor import for_each_block


logging_format = '%(asctime)-15s %(levelname)-8s %(name)-6s %(message)s'
logging.basicConfig(format=logging_format, level=logging.INFO)

web3 = Web3(HTTPProvider(endpoint_uri=f"http://localhost:8545"))
web3.eth.defaultAccount = "0x002ca7F9b416B2304cDd20c26882d1EF5c53F611"
print(f"Gas price {web3.eth.gasPrice}")


def some_function():
    pass

for_each_block(web3, some_function)


time.sleep(100)
# each time the client receieves a new block the `new_block_callback`
# function will be called with the block hash.
