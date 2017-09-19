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

import asyncio
import json
import logging
import sys
from functools import total_ordering
from typing import Optional

import eth_utils
import pkg_resources
from keeper.api.numeric import Wad
from keeper.api.util import synchronize, next_nonce
from web3 import Web3, EthereumTesterProvider
from web3.utils.events import get_event_data

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

    def _on_event(self, contract, event, cls, handler):
        register_filter_thread(contract.on(event, None, self._event_callback(cls, handler, False)))

    def _past_events(self, contract, event, cls, number_of_past_blocks) -> list:
        events = []

        def handler(obj):
            events.append(obj)

        block_number = contract.web3.eth.blockNumber
        filter_params = {'fromBlock': max(block_number-number_of_past_blocks, 0), 'toBlock': block_number}
        thread = contract.pastEvents(event, filter_params, self._event_callback(cls, handler, True))
        register_filter_thread(thread)
        thread.join()
        return events

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
    """Represents Ethereum calldata.

    Attributes:
        value: Calldata as a string starting with `0x`.
    """
    def __init__(self, value):
        assert(isinstance(value, str))
        assert(value.startswith('0x'))
        self.value = value

    def as_bytes(self) -> bytes:
        """Return the calldata as a byte array."""
        return bytes.fromhex(self.value.replace('0x', ''))

    def __str__(self):
        return f"{self.value}"

    def __repr__(self):
        return f"Calldata('{self.value}')"

    def __hash__(self):
        return self.value.__hash__()

    def __eq__(self, other):
        assert(isinstance(other, Calldata))
        return self.value == other.value


class Invocation(object):
    """Single contract method invocation, to be used together with `TxManager`.

    Attributes:
        address: Contract address.
        calldata: The calldata of the invocation.
    """
    def __init__(self, address: Address, calldata: Calldata):
        assert(isinstance(address, Address))
        assert(isinstance(calldata, Calldata))
        self.address = address
        self.calldata = calldata


class Receipt:
    """Represents a confirmation of a successful Ethereum transaction.

    Attributes:
        transaction_hash: Hash of the Ethereum transaction.
        transfers: A list of ERC20 token transfers resulting from the execution
            of this Ethereum transaction. Each transfer is an instance of the
            `Transfer` class.
    """
    def __init__(self, transaction_hash: str, gas_used: int, transfers: list):
        assert(isinstance(transaction_hash, str))
        assert(isinstance(gas_used, int))
        assert(isinstance(transfers, list))
        self.transaction_hash = transaction_hash
        self.gas_used = gas_used
        self.transfers = transfers


class Transact:
    """Represents an Ethereum transaction before it gets executed."""

    logger = logging.getLogger('api')

    def __init__(self, origin, web3, abi, address, contract, function, parameters, extra=None):
        assert(isinstance(origin, object))
        assert(isinstance(web3, Web3))
        assert(isinstance(abi, object))
        assert(isinstance(address, Address))
        assert(isinstance(contract, object))
        assert(isinstance(function, str))
        assert(isinstance(parameters, list))

        self.origin = origin
        self.web3 = web3
        self.abi = abi
        self.address = address
        self.contract = contract
        self.function = function
        self.parameters = parameters
        self.extra = extra

    async def _async_transact(self, **kwargs):
        try:
            # First we try to estimate the gas usage of the transaction. If gas estimation fails
            # it means there is no point in sending the transaction, thus we fail instantly and
            # do not increment the nonce. If the estimation is successful, we pass the calculated
            # gas value (plus some `gas_buffer`) to the subsequent `transact` calls so it does not
            # try to estimate it again. If it would try to estimate it again it could turn out
            # this transaction will fail (another block might have been mined in the meantime for
            # example), which would mean we incremented the nonce but never used it.
            #
            # This is why gas estimation has to happen first and before the nonce gets incremented.
            gas_estimate = self.estimated_gas()

            # Get the next available nonce. `next_nonce()` takes pending transactions into account.
            nonce = next_nonce(self.web3, Address(self.web3.eth.defaultAccount))

            # Determine `gas`
            if 'gas' in kwargs:
                gas = kwargs['gas']
            elif 'gas_buffer' in kwargs:
                gas = gas_estimate + kwargs['gas_buffer']
            else:
                gas = gas_estimate + 100000

            # Determine `gas_price`
            try:
                gas_price = kwargs['gas_price']
            except:
                gas_price = None

            self.logger.info(f"Sending transaction {self.name()} with nonce={nonce}, gas={gas},"
                             f" gas_price={gas_price if gas_price is not None else 'default'}")
            tx_hash = self._func(nonce, gas, gas_price)
            receipt = await self._async_prepare_receipt(self.web3, tx_hash)
            if receipt:
                self.logger.info(f"Transaction {self.name()} was successful (tx_hash={tx_hash})")
            else:
                self.logger.warning(f"Transaction {self.name()} mined successfully but generated no single log"
                                    f" entry, assuming it has failed (tx_hash={tx_hash})")
            return receipt
        except:
            self.logger.warning(f"Transaction {self.name()} failed ({sys.exc_info()[1]})")
            return None

    async def _async_prepare_receipt(self, web3, transaction_hash):
        receipt = await self._async_wait_for_receipt(web3, transaction_hash)
        receipt_logs = receipt['logs']
        if (receipt_logs is not None) and (len(receipt_logs) > 0):
            transfers = []
            for receipt_log in receipt_logs:
                if len(receipt_log['topics']) > 0 and receipt_log['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                    from keeper.api.token import ERC20Token
                    transfer_abi = [abi for abi in ERC20Token.abi if abi.get('name') == 'Transfer'][0]
                    event_data = get_event_data(transfer_abi, receipt_log)
                    transfers.append(Transfer(token_address=Address(event_data['address']),
                                              from_address=Address(event_data['args']['from']),
                                              to_address=Address(event_data['args']['to']),
                                              value=Wad(event_data['args']['value'])))
            return Receipt(transaction_hash=transaction_hash, gas_used=receipt['gasUsed'], transfers=transfers)
        else:
            return None

    async def _async_wait_for_receipt(self, web3, transaction_hash):
        while True:
            receipt = web3.eth.getTransactionReceipt(transaction_hash)
            if receipt is not None and receipt['blockNumber'] is not None:
                return receipt
            await asyncio.sleep(0.25)

    def as_dict(self, dict_or_none):
        if dict_or_none is None:
            return {}
        else:
            return dict(**dict_or_none)

    def _func(self, nonce, gas, gas_price):
        if gas_price is None:
            gas_price_dict = {}
        else:
            gas_price_dict = {'gasPrice': gas_price}

        # Until https://github.com/pipermerriam/eth-testrpc/issues/98 issue is not resolved,
        # `eth-testrpc` does not handle the `nonce` parameter properly so we do have to
        # ignore it otherwise unit-tests will not pass. Hopefully we will be able to get
        # rid of it once the above issue is solved.
        if isinstance(self.web3.currentProvider, EthereumTesterProvider):
            nonce_dict = {}
        else:
            nonce_dict = {'nonce': nonce}

        return self.contract.\
            transact({**{'gas': gas}, **gas_price_dict, **nonce_dict, **self.as_dict(self.extra)}).\
            __getattr__(self.function)(*self.parameters)

    def estimated_gas(self):
        return self.contract.estimateGas(self.as_dict(self.extra)).__getattr__(self.function)(*self.parameters)

    def name(self) -> str:
        """Returns the nicely formatted name (description) of this pending Ethereum transaction.

        Returns:
            Nicely formatted name (description) of this pending Ethereum transaction.
        """
        name = f"{repr(self.origin)}.{self.function}({self.parameters})"
        return name if self.extra is None else name + f" with {self.extra}"

    def transact(self, **kwargs) -> Optional[Receipt]:
        """Executes the Ethereum transaction synchronously.

        Executes the Ethereum transaction synchronously. The method will block until the
        transaction gets mined i.e. it will return when either the transaction execution
        succeeded or failed. In case of the former, a `Receipt` object will be returned.

        Out-of-gas exceptions are automatically recognized as transaction failures.

        Args:
            Additional arguments impacting how the Ethereum transaction gets executed.
            Allowed arguments are: `gas`, `gas_buffer`, `gas_price`.

        Returns:
            A `Receipt` object if the transaction invocation was successful. `None` otherwise.
        """
        return synchronize([self.transact_async(**kwargs)])[0]

    async def transact_async(self, **kwargs) -> Optional[Receipt]:
        """Executes the Ethereum transaction asynchronously.

        Executes the Ethereum transaction asynchronously. The method will return immediately.
        Ultimately, its future value will become either a `Receipt` or `None`, depending on
        whether the transaction execution was successful or not.

        Out-of-gas exceptions are automatically recognized as transaction failures.

        Args:
            Additional arguments impacting how the Ethereum transaction gets executed.
            Allowed arguments are: `gas`, `gas_buffer`, `gas_price`.

        Returns:
            A future value of either a `Receipt` object if the transaction invocation
            was successful, or `None` if it failed.
        """
        return await self._async_transact(**kwargs)

    def invocation(self) -> Invocation:
        """Returns the `Invocation` object for this pending Ethereum transaction.

        The :py:class:`keeper.api.Invocation` object may be used with :py:class:`keeper.api.transact.TxManager`
        to invoke multiple contract calls in one Ethereum transaction.

        Please see :py:class:`keeper.api.transact.TxManager` documentation for more details.

        Returns:
            :py:class:`keeper.api.Invocation` object for this pending Ethereum transaction.
        """
        return Invocation(self.address,
                          Calldata(self.web3.eth.contract(abi=self.abi).encodeABI(self.function, self.parameters)))


class Transfer:
    """Represents an ERC20 token transfer.

    Designed to enable monitoring transfers resulting from contract method execution.
    A list of transfers can be found in the :py:class:`keeper.api.Receipt` class.

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
