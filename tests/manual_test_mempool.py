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
import math
import os
import sys
import time
import threading
from pprint import pprint
from typing import Optional
from web3 import Web3

from pymaker import _get_endpoint_behavior, _track_status, Address, eth_transfer, NonceCalculation, Receipt, \
    Transact, Wad, web3_via_http
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
    stuck_txes_to_submit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
else:
    our_address = None
    stuck_txes_to_submit = 0

GWEI = 1000000000
# TODO: Dynamically choose prices based upon current block's base fee
too_low_gas = FixedGasPrice(gas_price=int(24 * GWEI), max_fee=None, tip=None)


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
            return list(map(lambda item: PendingTransact(web3=web3,
                                                         address=Address(item['from']),
                                                         nonce=int(item['nonce'], 16),
                                                         current_gas=int(item['gasPrice'], 16)), items))
        else:
            summarize_transactions(items)
    else:
        items = web3.manager.request_blocking("eth_getBlockByNumber", ["pending", True])['transactions']
        summarize_transactions(items)
        if address:
            items = filter(lambda item: item['from'].lower() == address.address.lower(), items)
            return list(map(lambda item: PendingTransact(web3=web3,
                                                         address=Address(item['from']),
                                                         nonce=item['nonce'],
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


class PendingTransact(Transact):
    """ Models a pending transaction retrieved from the mempool.

    These can be created by a call to `get_pending_transactions`, enabling the consumer to implement logic which
    cancels pending transactions upon keeper/bot startup.
    """
    def __init__(self, web3: Web3, address: Address, nonce: int, current_gas: int):
        assert isinstance(current_gas, int)
        super().__init__(origin=None, web3=web3, abi=None, address=address, contract=None,
                         function_name=None, parameters=None)
        self.nonce = nonce
        self.current_gas = current_gas

    def name(self):
        return f"Pending TX with nonce {self.nonce} and gas at {self.current_gas/GWEI} gwei"

    @_track_status
    async def transact_async(self, **kwargs) -> Optional[Receipt]:
        # TODO: Read transaction data from chain, create a new state machine to manage gas for the transaction.
        raise NotImplementedError()

    def cancel(self):
        return synchronize([self.cancel_async()])[0]

    async def cancel_async(self):
        initial_time = time.time()

        supports_eip1559 = _get_endpoint_behavior(web3).supports_eip1559
        tx_type = 0  # TODO: Pass gas details into ctor so we know the TX type.

        # Transaction lock isn't needed here, as we are replacing an existing nonce
        if supports_eip1559 and tx_type == 2:
            # TODO: Consider multiplying base_fee by 1.2 here to mitigate potential increase in subsequent blocks.
            base_fee = int(self.web3.eth.get_block('pending')['baseFeePerGas'])
            bumped_tip = math.ceil(min(1*GWEI, self.current_gas-base_fee) * 1.125)
            gas_fees = {'maxFeePerGas': base_fee + bumped_tip, 'maxPriorityFeePerGas': bumped_tip}
            tx_hash = bytes_to_hexstring(self.web3.eth.sendTransaction({'from': self.address.address,
                                                                        'to': self.address.address,
                                                                        **gas_fees,
                                                                        'nonce': self.nonce,
                                                                        'value': 0}))
        else:
            bumped_gas = math.ceil(self.current_gas * 1.125)
            gas_fees = {'gasPrice': bumped_gas}
            tx_hash = bytes_to_hexstring(self.web3.eth.sendTransaction({'from': self.address.address,
                                                                        'to': self.address.address,
                                                                        **gas_fees,
                                                                        'nonce': self.nonce,
                                                                        'value': 0}))
        self.logger.info(f"Cancelling tx with nonce={self.nonce}, gas_fees={gas_fees} (tx_hash={tx_hash})")


class TestApp:
    def main(self):
        print(f"Connected to {os.environ['ETH_RPC_URL']} at block {web3.eth.get_block('latest').number}")
        pending_txes = get_pending_transactions(web3, our_address)

        if our_address:
            print(f"{our_address} TX count is {web3.eth.getTransactionCount(our_address.address, block_identifier='pending')}")
            pprint(list(map(lambda t: f"{t.name()} with gas {t.current_gas}", pending_txes)))
            if len(pending_txes) > 0:
                # User would implement their own cancellation logic here, which could involve waiting before
                # submitting subsequent cancels.
                for tx in pending_txes:
                    if tx.current_gas < 20 * GWEI:
                        print(f"Attempting to cancel TX with nonce={tx.nonce}")
                        tx.cancel()
                    else:
                        print(f"Gas for TX with nonce={tx.nonce} is too high; leaving alone")

            if stuck_txes_to_submit:
                logging.info(f"Submitting {stuck_txes_to_submit} transactions with low gas")
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
