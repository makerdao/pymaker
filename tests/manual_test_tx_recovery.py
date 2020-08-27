# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2020 EdNoepel
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

import asyncio
import logging
import os
import sys
import time
import threading
from pprint import pprint

from pymaker import Address, get_pending_transactions, Wad, web3_via_http
from pymaker.deployment import DssDeployment
from pymaker.gas import FixedGasPrice, GeometricGasPrice
from pymaker.keys import register_keys

logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
# reduce logspew
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger("web3").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("requests").setLevel(logging.INFO)

pool_size = int(sys.argv[3]) if len(sys.argv) > 3 else 10
web3 = web3_via_http(endpoint_uri=os.environ['ETH_RPC_URL'])
web3.eth.defaultAccount = sys.argv[1]   # ex: 0x0000000000000000000000000000000aBcdef123
register_keys(web3, [sys.argv[2]])      # ex: key_file=~keys/default-account.json,pass_file=~keys/default-account.pass
our_address = Address(web3.eth.defaultAccount)
weth = DssDeployment.from_node(web3).collaterals['ETH-A'].gem

GWEI = 1000000000
increasing_gas = GeometricGasPrice(initial_price=int(1 * GWEI), every_secs=30, coefficient=1.5, max_price=100 * GWEI)


class TestApp:
    def main(self):
        self.startup()

        pending_txes = get_pending_transactions(web3)
        pprint(list(map(lambda t: f"{t.name()} with gas {t.current_gas}", pending_txes)))

        if len(pending_txes) > 0:
            while len(pending_txes) > 0:
                pending_txes[0].cancel(gas_price=increasing_gas)
                # After the synchronous cancel, wait to see if subsequent transactions get mined
                time.sleep(15)
                pending_txes = get_pending_transactions(web3)
        else:
            logging.info("No pending transactions were found; submitting one")
            self._run_future(weth.deposit(Wad(1)).transact_async(gas_price=FixedGasPrice(int(0.4 * GWEI))))
            time.sleep(0.5)

        self.shutdown()

    def startup(self):
        pass

    def shutdown(self):
        pass

    @staticmethod
    def _run_future(future):
        def worker():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                asyncio.get_event_loop().run_until_complete(future)
            finally:
                loop.close()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()


if __name__ == '__main__':
    TestApp().main()
