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
from web3.middleware import geth_poa_middleware

from pymaker import Address, eth_transfer
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

endpoint_uri = sys.argv[1]              # ex: https://localhost:8545
web3 = Web3(HTTPProvider(endpoint_uri=endpoint_uri, request_kwargs={"timeout": 30}))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
print(web3.clientVersion)

if len(sys.argv) > 3:
    web3.eth.defaultAccount = sys.argv[2]  # ex: 0x0000000000000000000000000000000aBcdef123
    register_keys(web3, [sys.argv[3]])      # ex: key_file=~keys/default-account.json,pass_file=~keys/default-account.pass
    our_address = Address(web3.eth.defaultAccount)
    run_transactions = True
elif len(sys.argv) > 2:
    our_address = Address(sys.argv[2])
    run_transactions = False
else:
    our_address = None
    run_transactions = False

eth = EthToken(web3, Address.zero())


class TestApp:
    def main(self):
        with Lifecycle(web3) as lifecycle:
            lifecycle.on_block(self.on_block)

    def on_block(self):
        if run_transactions:
            # dummy transaction: send 0 ETH to ourself
            eth_transfer(web3=web3, to=our_address, amount=Wad(0)).transact(from_address=our_address, gas=21000)
        else:
            logging.info(f"Found block; web3.eth.blockNumber={web3.eth.blockNumber}")
        if our_address:
            logging.info(f"Eth balance is {eth.balance_of(our_address)}")


if __name__ == '__main__':
    TestApp().main()
