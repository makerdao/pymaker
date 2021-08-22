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


logging.basicConfig(format='%(asctime)-15s [%(thread)d] %(levelname)-8s %(message)s', level=logging.DEBUG)
# reduce logspew
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger("web3").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("requests").setLevel(logging.INFO)

transact = False
web3 = web3_via_http(endpoint_uri=os.environ['ETH_RPC_URL'])
if len(sys.argv) > 1:
    web3.eth.defaultAccount = sys.argv[1]   # ex: 0x0000000000000000000000000000000aBcdef123
    if len(sys.argv) > 2:
        register_keys(web3, [sys.argv[2]])  # ex: key_file=~keys/default-account.json,pass_file=~keys/default-account.pass
        transact = True
    our_address = Address(web3.eth.defaultAccount)
    stuck_txes_to_submit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
else:
    our_address = None
    stuck_txes_to_submit = 0

GWEI = 1000000000
base_fee = int(web3.eth.get_block('pending')['baseFeePerGas'])
# Uses a type 0 TX
low_gas_type0 = FixedGasPrice(gas_price=base_fee, max_fee=None, tip=None)
# Forces a type 2 TX (erroring out if not supported by node)
tip = 1*GWEI
low_gas_type2 = FixedGasPrice(gas_price=None, max_fee=int(base_fee * 0.9) + tip, tip=tip)
# Favors a type 2 TX if the node supports it, otherwise falls back to a type 0 TX
low_gas_nodechoice = FixedGasPrice(low_gas_type0.gas_price, low_gas_type2.max_fee, low_gas_type2.tip)
low_gas = low_gas_nodechoice
print(f"Base fee is {base_fee/GWEI}; using {low_gas} for low gas")


def get_pending_transactions(web3: Web3, address: Address = None) -> list:
    """Retrieves a list of pending transactions from the mempool.

    Default OpenEthereum configurations gossip and then drop transactions which do not exceed the base fee.
    Third-party node providers (such as Infura) assign endpoints round-robin, such that the mempool on the node you've
    connected to has no relationship to the node where your TX was submitted.
    """
    assert isinstance(web3, Web3)
    assert isinstance(address, Address) or address is None

    # Get the list of pending transactions and their details from specified sources
    nonce_calc = _get_endpoint_behavior(web3).nonce_calc
    if nonce_calc == NonceCalculation.PARITY_NEXTNONCE:
        items = web3.manager.request_blocking("parity_pendingTransactions", [])
        if address:
            items = filter(lambda item: item['from'].lower() == address.address.lower(), items)
            return list(map(lambda item:
                PendingTransact(web3=web3,
                                address=Address(item['from']),
                                nonce=int(item['nonce'], 16),
                                gas_price=int(item['gasPrice'], 16),
                                gas_feecap=int(item['maxFeePerGas'], 16) if 'maxFeePerGas' in item else None,
                                gas_tip=int(item['maxPriorityFeePerGas'], 16) if 'maxPriorityFeePerGas' in item else None), items))
        else:
            summarize_transactions(items)
    else:
        items = web3.manager.request_blocking("eth_getBlockByNumber", ["pending", True])['transactions']
        summarize_transactions(items)
        if address:
            items = filter(lambda item: item['from'].lower() == address.address.lower(), items)

            return list(map(lambda item:
                PendingTransact(web3=web3,
                                address=Address(item['from']),
                                nonce=item['nonce'],
                                gas_price=item['gasPrice'],
                                gas_feecap=item['maxFeePerGas'] if 'maxFeePerGas' in item else None,
                                gas_tip=item['maxPriorityFeePerGas'] if 'maxPriorityFeePerGas' in item else None), items))
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
    print(f"This node's mempool contains {len(txes)} TXes from {len(addresses)} unique addresses "
          f"with gas from {lowest_gas} to {highest_gas} gwei")


class PendingTransact(Transact):
    """ Models a pending transaction retrieved from the mempool.

    These can be created by a call to `get_pending_transactions`, enabling the consumer to implement logic which
    cancels pending transactions upon keeper/bot startup.
    """
    def __init__(self, web3: Web3, address: Address, nonce: int, gas_price: int, gas_feecap: int = None, gas_tip: int = None):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)
        assert isinstance(nonce, int)
        assert isinstance(gas_price, int)
        assert isinstance(gas_feecap, int) or gas_feecap is None
        assert isinstance(gas_tip, int) or gas_tip is None

        super().__init__(origin=None, web3=web3, abi=None, address=address, contract=None,
                         function_name=None, parameters=None)
        self.nonce = nonce
        self.gas_price = gas_price
        self.gas_feecap = gas_feecap
        self.gas_tip = gas_tip

    def name(self):
        return f"Pending TX with nonce {self.nonce} and gas_price={self.gas_price} gas_feecap={self.gas_feecap} gas_tip={self.gas_tip}"

    @_track_status
    async def transact_async(self, **kwargs) -> Optional[Receipt]:
        # TODO: Read transaction data from chain, create a new state machine to manage gas for the transaction.
        raise NotImplementedError()

    def cancel(self):
        return synchronize([self.cancel_async()])[0]

    async def cancel_async(self):
        supports_eip1559 = _get_endpoint_behavior(web3).supports_eip1559
        # Transaction lock isn't needed here, as we are replacing an existing nonce
        if self.gas_feecap and self.gas_tip:
            assert supports_eip1559
            base_fee = int(self.web3.eth.get_block('pending')['baseFeePerGas'])
            bumped_tip = math.ceil(min(1 * GWEI, self.gas_tip) * 1.125)
            bumped_feecap = max(base_fee + bumped_tip, math.ceil((self.gas_feecap + bumped_tip) * 1.125))
            gas_fees = {'maxFeePerGas': bumped_feecap, 'maxPriorityFeePerGas': bumped_tip}
            # CAUTION: On OpenEthereum//v3.3.0-rc.4, this produces an underpriced gas error; even when multiplying by 2
        else:
            assert False
            if supports_eip1559:
                base_fee = math.ceil(self.web3.eth.get_block('pending')['baseFeePerGas'])
                bumped_tip = math.ceil(min(1 * GWEI, self.gas_price - base_fee) * 1.125)
                gas_fees = {'maxFeePerGas': math.ceil((self.gas_price + bumped_tip) * 1.25), 'maxPriorityFeePerGas': bumped_tip}
            else:
                bumped_gas = math.ceil(self.gas_price * 1.125)
                gas_fees = {'gasPrice': bumped_gas}
        self.logger.info(f"Attempting to cancel TX with nonce={self.nonce} using gas_fees={gas_fees}")
        tx_hash = bytes_to_hexstring(self.web3.eth.sendTransaction({'from': self.address.address,
                                                                    'to': self.address.address,
                                                                    **gas_fees,
                                                                    'nonce': self.nonce,
                                                                    'value': 0}))
        self.logger.info(f"Cancelled TX with nonce={self.nonce}; TX hash: {tx_hash}")

class TestApp:
    def main(self):
        print(f"Connected to {os.environ['ETH_RPC_URL']} at block {web3.eth.get_block('latest').number}")
        pending_txes = get_pending_transactions(web3, our_address)

        if our_address:
            print(f"{our_address} TX count is {web3.eth.getTransactionCount(our_address.address, block_identifier='pending')}")
            pprint(list(map(lambda t: f"{t.name()}", pending_txes)))
            if transact and len(pending_txes) > 0:
                # User would implement their own cancellation logic here, which could involve waiting before
                # submitting subsequent cancels.
                for tx in pending_txes:
                    if tx.gas_price < 100 * GWEI:
                        tx.cancel()
                    else:
                        print(f"Gas for TX with nonce={tx.nonce} is too high; leaving alone")

            if transact and stuck_txes_to_submit:
                logging.info(f"Submitting {stuck_txes_to_submit} transactions with low gas")
                for i in range(1, stuck_txes_to_submit+1):
                    self._run_future(eth_transfer(web3=web3, to=our_address, amount=Wad(i*10)).transact_async(
                        gas_strategy=low_gas))
            time.sleep(2)  # Give event loop a chance to send the transactions

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
