# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2020-2021 EdNoepel
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
import os
import sys
from web3 import Web3, HTTPProvider

from pymaker import Address, eth_transfer, web3_via_http
from pymaker.gas import DefaultGasPrice, GeometricGasPrice
from pymaker.lifecycle import Lifecycle
from pymaker.keys import register_keys
from pymaker.numeric import Wad
from pymaker.token import EthToken

logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.DEBUG)
# reduce logspew
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger("web3").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("requests").setLevel(logging.INFO)

endpoint_uri = sys.argv[1]
web3 = web3_via_http(endpoint_uri, timeout=10)
print(web3.clientVersion)

"""
Argument:           Reqd?   Example:
Ethereum node URI   yes     https://localhost:8545
Ethereum address    no      0x0000000000000000000000000000000aBcdef123
Private key         no      key_file=~keys/default-account.json,pass_file=~keys/default-account.pass
Gas price (GWEI)    no      9
"""


if len(sys.argv) > 3:
    web3.eth.defaultAccount = sys.argv[2]
    register_keys(web3, [sys.argv[3]])
    our_address = Address(web3.eth.defaultAccount)
    run_transactions = True
elif len(sys.argv) > 2:
    our_address = Address(sys.argv[2])
    run_transactions = False
else:
    our_address = None
    run_transactions = False

gas_strategy = DefaultGasPrice() if len(sys.argv) <= 4 else \
    GeometricGasPrice(initial_price=None,  # int(float(sys.argv[4]) * GeometricGasPrice.GWEI),
                      initial_feecap=int(60 * GeometricGasPrice.GWEI),
                      initial_tip=int(2 * GeometricGasPrice.GWEI),
                      every_secs=2,
                      max_price=100 * GeometricGasPrice.GWEI)

eth = EthToken(web3, Address.zero())


class TestApp:
    def main(self):
        with Lifecycle(web3) as lifecycle:
            lifecycle.on_block(self.on_block)

    def on_block(self):
        block = web3.eth.blockNumber
        logging.info(f"Found block; web3.eth.blockNumber={block}")

        if run_transactions and block % 3 == 0:
            # dummy transaction: send 0 ETH to ourself
            eth_transfer(web3=web3, to=our_address, amount=Wad(0)).transact(
                from_address=our_address, gas=21000, gas_strategy=gas_strategy)

        if our_address:
            logging.info(f"Eth balance is {eth.balance_of(our_address)}")


if __name__ == '__main__':
    TestApp().main()
