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
from typing import Optional
from web3 import Web3

from pymaker import _get_endpoint_behavior, _track_status, Address, eth_transfer, NonceCalculation, Receipt, \
    Transact, Wad, web3_via_http
from pymaker.deployment import DssDeployment
from pymaker.gas import FixedGasPrice, GasStrategy, GeometricGasPrice
from pymaker.keys import register_keys
from pymaker.util import synchronize, bytes_to_hexstring


logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.DEBUG)
# reduce logspew
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger("web3").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("requests").setLevel(logging.INFO)

web3 = web3_via_http(endpoint_uri=os.environ['ETH_RPC_URL'])
if len(sys.argv) > 2:
    web3.eth.defaultAccount = sys.argv[1]   # ex: 0x0000000000000000000000000000000aBcdef123
    register_keys(web3, [sys.argv[2]])      # ex: key_file=~keys/default-account.json,pass_file=~keys/default-account.pass
    our_address = Address(web3.eth.defaultAccount)
    stuck_txes_to_submit = int(sys.argv[3]) if len(sys.argv) > 3 else 1
else:
    our_address = None
    stuck_txes_to_submit = 0

GWEI = 1000000000
too_low_gas = FixedGasPrice(gas_price=int(0.4 * GWEI), max_fee=None, tip=None)
increasing_gas = GeometricGasPrice(web3=web3, initial_price=1*GWEI, initial_tip=None,
                                   every_secs=30, coefficient=1.5, max_price=200*GWEI)


def get_pending_transactions(web3: Web3, address: Address = None) -> list:
    """Retrieves a list of pending transactions from the mempool."""
    assert isinstance(web3, Web3)
    assert isinstance(address, Address) or address is None

    # Get the list of pending transactions and their details from specified sources
    nonce_calc = _get_endpoint_behavior(web3).nonce_calc
    if nonce_calc == NonceCalculation.PARITY_NEXTNONCE:
        items = web3.manager.request_blocking("parity_pendingTransactions", [])
        if address:
            items = filter(lambda item: item['from'].lower() == address.address.lower(), items)
            return list(map(lambda item: RecoveredTransact(web3=web3,
                                                           address=Address(item['from']),
                                                           nonce=int(item['nonce'], 16),
                                                           latest_tx_hash=item['hash'],
                                                           current_gas=int(item['gasPrice'], 16)), items))
        else:
            summarize_transactions(items)
    else:
        items = web3.manager.request_blocking("eth_getBlockByNumber", ["pending", True])['transactions']
        summarize_transactions(items)
        if address:
            items = filter(lambda item: item['from'].lower() == address.address.lower(), items)
            return list(map(lambda item: RecoveredTransact(web3=web3,
                                                           address=Address(item['from']),
                                                           nonce=item['nonce'],
                                                           latest_tx_hash=item['hash'],
                                                           current_gas=item['gasPrice']), items))
        else:
            summarize_transactions(items)
    return []


def summarize_transactions(txes):
    if len(txes) == 0:
        print("No transactions found")
        return
    lowest_gas = None
    highest_gas = None
    addresses = set()
    for tx in txes:
        if isinstance(tx['gasPrice'], int):
            gas_price = tx['gasPrice'] / GasStrategy.GWEI
        else:
            gas_price = int(tx['gasPrice'], 16) / GasStrategy.GWEI
        lowest_gas = min(lowest_gas, gas_price) if lowest_gas else gas_price
        highest_gas = max(highest_gas, gas_price) if highest_gas else gas_price
        addresses.add(tx['from'])
        # pprint(tx)
    print(f"Found {len(txes)} TXes from {len(addresses)} unique addresses "
          f"with gas from {lowest_gas} to {highest_gas} gwei")


class RecoveredTransact(Transact):
    """ Models a pending transaction retrieved from the mempool.

    These can be created by a call to `get_pending_transactions`, enabling the consumer to implement logic which
    cancels pending transactions upon keeper/bot startup.
    """
    def __init__(self, web3: Web3,
                 address: Address,
                 nonce: int,
                 latest_tx_hash: str,
                 current_gas: int):
        assert isinstance(current_gas, int)
        super().__init__(origin=None,
                         web3=web3,
                         abi=None,
                         address=address,
                         contract=None,
                         function_name=None,
                         parameters=None)
        self.nonce = nonce
        self.tx_hashes.append(latest_tx_hash)
        self.current_gas = current_gas
        self.gas_price_last = None

    def name(self):
        return f"Recovered tx with nonce {self.nonce}"

    @_track_status
    async def transact_async(self, **kwargs) -> Optional[Receipt]:
        # TODO: Read transaction data from chain, create a new state machine to manage gas for the transaction.
        raise NotImplementedError()

    def cancel(self, gas_strategy: GasStrategy):
        return synchronize([self.cancel_async(gas_strategy)])[0]

    async def cancel_async(self, gas_strategy: GasStrategy):
        assert isinstance(gas_strategy, GasStrategy)
        initial_time = time.time()
        self.gas_price_last = self.current_gas
        self.tx_hashes.clear()

        if gas_strategy.get_gas_price(0) <= self.current_gas * 1.125:
            self.logger.warning(f"Recovery gas price is less than current gas price {self.current_gas}; "
                                "cancellation will be deferred until the strategy produces an acceptable price.")

        while True:
            seconds_elapsed = int(time.time() - initial_time)
            gas_price_value = gas_strategy.get_gas_price(seconds_elapsed)
            if gas_price_value > self.gas_price_last * 1.125:
                self.gas_price_last = gas_price_value
                # Transaction lock isn't needed here, as we are replacing an existing nonce
                tx_hash = bytes_to_hexstring(self.web3.eth.sendTransaction({'from': self.address.address,
                                                                            'to': self.address.address,
                                                                            'gasPrice': gas_price_value,
                                                                            'nonce': self.nonce,
                                                                            'value': 0}))
                self.tx_hashes.append(tx_hash)
                self.logger.info(f"Attempting to cancel recovered tx with nonce={self.nonce}, "
                                 f"gas_price={gas_price_value} (tx_hash={tx_hash})")

            for tx_hash in self.tx_hashes:
                receipt = self._get_receipt(tx_hash)
                if receipt:
                    self.logger.info(f"{self.name()} was cancelled (tx_hash={tx_hash})")
                    return

            await asyncio.sleep(0.75)


class TestApp:
    def main(self):
        print(f"Connected to {os.environ['ETH_RPC_URL']}")
        pending_txes = get_pending_transactions(web3, our_address)

        if our_address:
            pprint(list(map(lambda t: f"{t.name()} with gas {t.current_gas}", pending_txes)))
            if len(pending_txes) > 0:
                while len(pending_txes) > 0:
                    pending_txes[0].cancel(gas_strategy=increasing_gas)
                    # After the synchronous cancel, wait to see if subsequent transactions get mined
                    time.sleep(15)
                    pending_txes = get_pending_transactions(web3)
            else:
                logging.info(f"No pending transactions were found; submitting {stuck_txes_to_submit}")
                for i in range(1, stuck_txes_to_submit+1):
                    self._run_future(eth_transfer(web3=web3, to=our_address, amount=Wad(0)).transact_async(
                        gas_strategy=too_low_gas))
                time.sleep(2)

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
