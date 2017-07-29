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

import json
import time
from functools import total_ordering

import asyncio
import eth_utils
import logging
import pkg_resources
import sys

from web3 import Web3
from web3.utils.events import get_event_data

from api.numeric import Wad


filter_threads = []


def register_filter_thread(filter_thread):
    filter_threads.append(filter_thread)


def any_filter_thread_present() -> bool:
    return len(filter_threads) > 0


def all_filter_threads_alive() -> bool:
    return all(filter_thread_alive(filter_thread) for filter_thread in filter_threads)


def filter_thread_alive(filter_thread) -> bool:
    # it's a wicked way of detecting whether a web3.py filter is still working
    # but unfortunately I wasn't able to find any other one
    return hasattr(filter_thread, '_args') and hasattr(filter_thread, '_kwargs') or not filter_thread.running


def stop_all_filter_threads():
    for filter_thread in filter_threads:
        try:
            filter_thread.stop_watching(timeout=60)
        except:
            pass


@total_ordering
class Address:
    """Represents an Ethereum address.

    Addresses get normalized automatically, so instances of this class can be safely compared to each other.

    Args:
        address: Can be any address representation allowed by web3.py
            or another instance of the Address class.

    Attributes:
        address: Normalized hexadecimal representation of the Ethereum address.
    """
    def __init__(self, address):
        if isinstance(address, Address):
            self.address = address.address
        else:
            self.address = eth_utils.to_normalized_address(address)

    def as_bytes(self) -> bytes:
        """Return the address as a 20-byte bytes array."""
        return bytes.fromhex(self.address.replace('0x', ''))

    def __str__(self):
        return f"{self.address}"

    def __repr__(self):
        return f"Address('{self.address}')"

    def __hash__(self):
        return self.address.__hash__()

    def __eq__(self, other):
        assert(isinstance(other, Address))
        return self.address == other.address

    def __lt__(self, other):
        assert(isinstance(other, Address))
        return self.address < other.address


class Contract:
    logger = logging.getLogger('api')

    @staticmethod
    def _deploy(web3: Web3, abi: dict, bytecode: str, args) -> Address:
        contract_factory = web3.eth.contract(abi=abi, bytecode=bytecode)
        tx_hash = contract_factory.deploy(args=args)
        receipt = web3.eth.getTransactionReceipt(tx_hash)
        return Address(receipt['contractAddress'])

    def _assert_contract_exists(self, web3, address):
        code = web3.eth.getCode(address.address)
        if (code == "0x") or (code is None):
            raise Exception(f"No contract found at {address}")

    def _wait_for_receipt(self, web3, transaction_hash):
        while True:
            receipt = web3.eth.getTransactionReceipt(transaction_hash)
            if receipt is not None and receipt['blockNumber'] is not None:
                return receipt
            time.sleep(0.25)

    async def _async_wait_for_receipt(self, web3, transaction_hash):
        while True:
            receipt = web3.eth.getTransactionReceipt(transaction_hash)
            if receipt is not None and receipt['blockNumber'] is not None:
                return receipt
            await asyncio.sleep(0.25)

    def _on_event(self, contract, event, cls, handler):
        register_filter_thread(contract.on(event, None, self._event_callback(cls, handler, False)))

    def _past_events(self, contract, event, cls, number_of_past_blocks) -> list:
        events = []

        def handler(obj):
            events.append(obj)

        block_number = contract.web3.eth.blockNumber
        filter_params = {'fromBlock': block_number-number_of_past_blocks, 'toBlock': block_number-1}
        thread = contract.pastEvents(event, filter_params, self._event_callback(cls, handler, True))
        register_filter_thread(thread)
        thread.join()
        return events

    def _transact(self, web3, log_message, func):
        try:
            self.logger.info(f"Transaction {log_message} in progress...")
            tx_hash = func()
            receipt = self._prepare_receipt(web3, tx_hash)
            if receipt:
                self.logger.info(f"Transaction {log_message} was successful (tx_hash={receipt.transaction_hash})")
            else:
                self.logger.warning(f"Transaction {log_message} failed")
            return receipt
        except:
            self.logger.warning(f"Transaction {log_message} failed ({sys.exc_info()[1]})")
            return None

    async def _async_transact(self, web3, log_message, func):
        try:
            self.logger.info(f"Transaction {log_message} in progress...")
            tx_hash = func()
            receipt = await self._async_prepare_receipt(web3, tx_hash)
            if receipt:
                self.logger.info(f"Transaction {log_message} was successful (tx_hash={receipt.transaction_hash})")
            else:
                self.logger.warning(f"Transaction {log_message} failed")
            return receipt
        except:
            self.logger.warning(f"Transaction {log_message} failed ({sys.exc_info()[1]})")
            return None

    def _prepare_receipt(self, web3, transaction_hash):
        receipt = self._wait_for_receipt(web3, transaction_hash)
        receipt_logs = receipt['logs']
        if (receipt_logs is not None) and (len(receipt_logs) > 0):
            transfers = []
            for receipt_log in receipt_logs:
                if len(receipt_log['topics']) > 0 and receipt_log['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                    from api.token import ERC20Token
                    transfer_abi = [abi for abi in ERC20Token.abi if abi.get('name') == 'Transfer'][0]
                    event_data = get_event_data(transfer_abi, receipt_log)
                    transfers.append(Transfer(token_address=Address(event_data['address']),
                                              from_address=Address(event_data['args']['from']),
                                              to_address=Address(event_data['args']['to']),
                                              value=Wad(event_data['args']['value'])))
            return Receipt(transaction_hash=transaction_hash, transfers=transfers)
        else:
            return None

    async def _async_prepare_receipt(self, web3, transaction_hash):
        receipt = await self._async_wait_for_receipt(web3, transaction_hash)
        receipt_logs = receipt['logs']
        if (receipt_logs is not None) and (len(receipt_logs) > 0):
            transfers = []
            for receipt_log in receipt_logs:
                if len(receipt_log['topics']) > 0 and receipt_log['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                    from api.token import ERC20Token
                    transfer_abi = [abi for abi in ERC20Token.abi if abi.get('name') == 'Transfer'][0]
                    event_data = get_event_data(transfer_abi, receipt_log)
                    transfers.append(Transfer(token_address=Address(event_data['address']),
                                              from_address=Address(event_data['args']['from']),
                                              to_address=Address(event_data['args']['to']),
                                              value=Wad(event_data['args']['value'])))
            return Receipt(transaction_hash=transaction_hash, transfers=transfers)
        else:
            return None

    def _event_callback(self, cls, handler, past):
        def callback(log):
            if past:
                self.logger.debug(f"Past event {log['event']} discovered, block_number={log['blockNumber']},"
                                 f" tx_hash={log['transactionHash']}")
            else:
                self.logger.debug(f"Event {log['event']} discovered, block_number={log['blockNumber']},"
                                 f" tx_hash={log['transactionHash']}")
            handler(cls(log['args']))
        return callback

    @staticmethod
    def _load_abi(package, resource) -> dict:
        return json.loads(pkg_resources.resource_string(package, resource))

    @staticmethod
    def _load_bin(package, resource) -> str:
        return pkg_resources.resource_string(package, resource)


class Calldata:
    """Represents Ethereum calldata."""
    def __init__(self, value):
        assert(isinstance(value, str))
        assert(value.startswith('0x'))
        self.str = value

    def as_bytes(self) -> bytes:
        """Return the calldata as a byte array."""
        return bytes.fromhex(self.str.replace('0x', ''))

    def __str__(self):
        return f"{self.str}"

    def __repr__(self):
        return f"Calldata('{self.str}')"

    def __hash__(self):
        return self.str.__hash__()

    def __eq__(self, other):
        assert(isinstance(other, Calldata))
        return self.str == other.str


class Receipt:
    """Represents a confirmation of a successful Ethereum transaction.

    Attributes:
        transaction_hash: Hash of the Ethereum transaction.
        transfers: A list of ERC20 token transfers resulting from the execution
            of this Ethereum transaction. Each transfer is an instance of the
            `Transfer` class.
    """
    def __init__(self, transaction_hash: str, transfers: list):
        assert(isinstance(transaction_hash, str))
        assert(isinstance(transfers, list))
        self.transaction_hash = transaction_hash
        self.transfers = transfers


class Transfer:
    """Represents an ERC20 token transfer.

    Designed to enable monitoring transfers resulting from smart contract method execution.
    A list of transfers can be found in the `Receipt` class.

    Attributes:
        token_address: Address of the ERC20 token that has been transferred.
        from_address: Source address of the transfer.
        to_address: Destination address of the transfer.
        value: Value transferred.
    """
    def __init__(self, token_address: Address, from_address: Address, to_address: Address, value: Wad):
        assert(isinstance(token_address, Address))
        assert(isinstance(from_address, Address))
        assert(isinstance(to_address, Address))
        assert(isinstance(value, Wad))
        self.token_address = token_address
        self.from_address = from_address
        self.to_address = to_address
        self.value = value

    @staticmethod
    def incoming(our_address: Address):
        return lambda transfer: transfer.to_address == our_address

    @staticmethod
    def outgoing(our_address: Address):
        return lambda transfer: transfer.from_address == our_address