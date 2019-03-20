# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
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
import re
import sys
import time
from enum import Enum, auto
from functools import total_ordering, wraps
from threading import Lock
from typing import Optional

import eth_utils
import pkg_resources
from hexbytes import HexBytes

from web3 import Web3
from web3.utils.contracts import get_function_info, encode_abi
from web3.utils.events import get_event_data

from pymaker.gas import DefaultGasPrice, GasPrice
from pymaker.numeric import Wad
from pymaker.util import synchronize, bytes_to_hexstring, is_contract_at

filter_threads = []
node_is_parity = None
transaction_lock = Lock()


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


def _track_status(f):
    @wraps(f)
    async def wrapper(*args, **kwds):
        # Check for multiple execution
        if args[0].status != TransactStatus.NEW:
            raise Exception("Each `Transact` can only be executed once")

        # Set current status to in progress
        args[0].status = TransactStatus.IN_PROGRESS

        try:
            return await f(*args, **kwds)
        finally:
            args[0].status = TransactStatus.FINISHED

    return wrapper


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
            self.address = eth_utils.to_checksum_address(address)

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
    logger = logging.getLogger()

    @staticmethod
    def _deploy(web3: Web3, abi: list, bytecode: str, args: list) -> Address:
        assert(isinstance(web3, Web3))
        assert(isinstance(abi, list))
        assert(isinstance(bytecode, str))
        assert(isinstance(args, list))

        contract = web3.eth.contract(abi=abi, bytecode=bytecode)
        tx_hash = contract.constructor(*args).transact(
            transaction={'from': eth_utils.to_checksum_address(web3.eth.defaultAccount)})
        receipt = web3.eth.getTransactionReceipt(tx_hash)
        return Address(receipt['contractAddress'])

    @staticmethod
    def _get_contract(web3: Web3, abi: list, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(abi, list))
        assert(isinstance(address, Address))

        if not is_contract_at(web3, address):
            raise Exception(f"No contract found at {address}")

        return web3.eth.contract(abi=abi)(address=address.address)

    def _past_events(self, contract, event, cls, number_of_past_blocks, event_filter) -> list:
        assert(isinstance(number_of_past_blocks, int))
        assert(isinstance(event_filter, dict) or (event_filter is None))

        def _event_callback(cls, past):
            def callback(log):
                if past:
                    self.logger.debug(f"Past event {log['event']} discovered, block_number={log['blockNumber']},"
                                      f" tx_hash={bytes_to_hexstring(log['transactionHash'])}")
                else:
                    self.logger.debug(f"Event {log['event']} discovered, block_number={log['blockNumber']},"
                                      f" tx_hash={bytes_to_hexstring(log['transactionHash'])}")
                return cls(log)

            return callback

        block_number = contract.web3.eth.blockNumber
        result = contract.events[event].createFilter(fromBlock=max(block_number-number_of_past_blocks, 0),
                                                     toBlock=block_number,
                                                     argument_filters=event_filter).get_all_entries()

        return list(map(_event_callback(cls, True), result))

    @staticmethod
    def _load_abi(package, resource) -> list:
        return json.loads(pkg_resources.resource_string(package, resource))

    @staticmethod
    def _load_bin(package, resource) -> str:
        return str(pkg_resources.resource_string(package, resource), "utf-8")


class Calldata:
    """Represents Ethereum calldata.

    Attributes:
        value: Calldata as either a string starting with `0x`, or as bytes.
    """
    def __init__(self, value):
        if isinstance(value, str):
            assert(value.startswith('0x'))
            self.value = value

        elif isinstance(value, bytes):
            self.value = bytes_to_hexstring(value)

        else:
            raise Exception(f"Unable to create calldata from '{value}'")

    @classmethod
    def from_signature(cls, fn_sign: str, fn_args: list):
        """ Allow to create a `Calldata` from a function signature and a list of arguments.

        :param fn_sign: the function signature ie. "function(uint256,address)"
        :param fn_args: arguments to the function ie. [123, "0x00...00"]
        :return:
        """
        assert isinstance(fn_sign, str)
        assert isinstance(fn_args, list)

        fn_split = re.split('[(),]', fn_sign)
        fn_name = fn_split[0]
        fn_args_type = [{"type": type} for type in fn_split[1:] if type]

        fn_abi = {"type": "function", "name": fn_name, "inputs": fn_args_type}
        fn_abi, fn_selector, fn_arguments = get_function_info("test", fn_abi=fn_abi, args=fn_args)

        calldata = encode_abi(Web3, fn_abi, fn_arguments, fn_selector)

        return cls(calldata)

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
    """Represents a receipt for an Ethereum transaction.

    Attributes:
        raw_receipt: Raw receipt received from the Ethereum node.
        transaction_hash: Hash of the Ethereum transaction.
        gas_used: Amount of gas used by the Ethereum transaction.
        transfers: A list of ERC20 token transfers resulting from the execution
            of this Ethereum transaction. Each transfer is an instance of the
            :py:class:`pymaker.Transfer` class.
        result: Transaction-specific return value (i.e. new order id for Oasis
            order creation transaction).
        successful: Boolean flag which is `True` if the Ethereum transaction
            was successful. We consider transaction successful if the contract
            method has been executed without throwing.
    """
    def __init__(self, receipt):
        self.raw_receipt = receipt
        self.transaction_hash = receipt['transactionHash']
        self.gas_used = receipt['gasUsed']
        self.transfers = []
        self.result = None

        receipt_logs = receipt['logs']
        if (receipt_logs is not None) and (len(receipt_logs) > 0):
            self.successful = True
            for receipt_log in receipt_logs:
                if len(receipt_log['topics']) > 0:
                    # $ seth keccak $(seth --from-ascii "Transfer(address,address,uint256)")
                    # 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef
                    if receipt_log['topics'][0] == HexBytes('0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'):
                        from pymaker.token import ERC20Token
                        transfer_abi = [abi for abi in ERC20Token.abi if abi.get('name') == 'Transfer'][0]
                        event_data = get_event_data(transfer_abi, receipt_log)
                        self.transfers.append(Transfer(token_address=Address(event_data['address']),
                                                       from_address=Address(event_data['args']['from']),
                                                       to_address=Address(event_data['args']['to']),
                                                       value=Wad(event_data['args']['value'])))

                    # $ seth keccak $(seth --from-ascii "Mint(address,uint256)")
                    # 0x0f6798a560793a54c3bcfe86a93cde1e73087d944c0ea20544137d4121396885
                    if receipt_log['topics'][0] == HexBytes('0x0f6798a560793a54c3bcfe86a93cde1e73087d944c0ea20544137d4121396885'):
                        from pymaker.token import DSToken
                        transfer_abi = [abi for abi in DSToken.abi if abi.get('name') == 'Mint'][0]
                        event_data = get_event_data(transfer_abi, receipt_log)
                        self.transfers.append(Transfer(token_address=Address(event_data['address']),
                                                       from_address=Address('0x0000000000000000000000000000000000000000'),
                                                       to_address=Address(event_data['args']['guy']),
                                                       value=Wad(event_data['args']['wad'])))

                    # $ seth keccak $(seth --from-ascii "Burn(address,uint256)")
                    # 0xcc16f5dbb4873280815c1ee09dbd06736cffcc184412cf7a71a0fdb75d397ca5
                    if receipt_log['topics'][0] == HexBytes('0xcc16f5dbb4873280815c1ee09dbd06736cffcc184412cf7a71a0fdb75d397ca5'):
                        from pymaker.token import DSToken
                        transfer_abi = [abi for abi in DSToken.abi if abi.get('name') == 'Burn'][0]
                        event_data = get_event_data(transfer_abi, receipt_log)
                        self.transfers.append(Transfer(token_address=Address(event_data['address']),
                                                       from_address=Address(event_data['args']['guy']),
                                                       to_address=Address('0x0000000000000000000000000000000000000000'),
                                                       value=Wad(event_data['args']['wad'])))

        else:
            self.successful = False

    @property
    def logs(self):
        return self.raw_receipt['logs']


class TransactStatus(Enum):
     NEW = auto()
     IN_PROGRESS = auto()
     FINISHED = auto()


class Transact:
    """Represents an Ethereum transaction before it gets executed."""

    logger = logging.getLogger()

    def __init__(self,
                 origin: Optional[object],
                 web3: Web3,
                 abi: Optional[list],
                 address: Address,
                 contract: Optional[object],
                 function_name: Optional[str],
                 parameters: Optional[list],
                 extra: Optional[dict] = None,
                 result_function=None):
        assert(isinstance(origin, object) or (origin is None))
        assert(isinstance(web3, Web3))
        assert(isinstance(abi, list) or (abi is None))
        assert(isinstance(address, Address))
        assert(isinstance(contract, object) or (contract is None))
        assert(isinstance(function_name, str) or (function_name is None))
        assert(isinstance(parameters, list) or (parameters is None))
        assert(isinstance(extra, dict) or (extra is None))
        assert(callable(result_function) or (result_function is None))

        self.origin = origin
        self.web3 = web3
        self.abi = abi
        self.address = address
        self.contract = contract
        self.function_name = function_name
        self.parameters = parameters
        self.extra = extra
        self.result_function = result_function
        self.status = TransactStatus.NEW
        self.nonce = None

    def _is_parity(self) -> bool:
        global node_is_parity
        if node_is_parity is None:
            node_is_parity = "parity" in self.web3.version.node.lower()

        return node_is_parity

    def _get_receipt(self, transaction_hash: str) -> Optional[Receipt]:
        raw_receipt = self.web3.eth.getTransactionReceipt(transaction_hash)
        if raw_receipt is not None and raw_receipt['blockNumber'] is not None:
            receipt = Receipt(raw_receipt)
            receipt.result = self.result_function(receipt) if self.result_function is not None else None

            return receipt

        else:
            return None

    def _as_dict(self, dict_or_none) -> dict:
        if dict_or_none is None:
            return {}
        else:
            return dict(**dict_or_none)

    def _gas(self, gas_estimate: int, **kwargs) -> int:
        if 'gas' in kwargs and 'gas_buffer' in kwargs:
            raise Exception('"gas" and "gas_buffer" keyword arguments may not be specified at the same time')

        if 'gas' in kwargs:
            return kwargs['gas']
        elif 'gas_buffer' in kwargs:
            return gas_estimate + kwargs['gas_buffer']
        else:
            return gas_estimate + 100000

    def _func(self, from_account: str, gas: int, gas_price: Optional[int], nonce: Optional[int]):
        gas_price_dict = {'gasPrice': gas_price} if gas_price is not None else {}
        nonce_dict = {'nonce': nonce} if nonce is not None else {}

        transaction_params = {**{'from': from_account, 'gas': gas},
                              **gas_price_dict,
                              **nonce_dict,
                              **self._as_dict(self.extra)}

        if self.contract is not None:
            if self.function_name is None:
                return self.web3.eth.sendTransaction({**transaction_params, **{'to': self.address.address,
                                                                               'data': self.parameters[0]}})

            else:
                return self._contract_function().transact(transaction_params)

        else:
            return self.web3.eth.sendTransaction({**transaction_params, **{'to': self.address.address}})

    def _contract_function(self):
        if '(' in self.function_name:
            function_factory = self.contract.get_function_by_signature(self.function_name)

        else:
            function_factory = self.contract.get_function_by_name(self.function_name)

        return function_factory(*self.parameters)

    def name(self) -> str:
        """Returns the nicely formatted name of this pending Ethereum transaction.

        Returns:
            Nicely formatted name of this pending Ethereum transaction.
        """
        if self.origin:
            def format_parameter(parameter):
                if isinstance(parameter, bytes):
                    return bytes_to_hexstring(parameter)
                else:
                    return parameter

            formatted_parameters = str(list(map(format_parameter, self.parameters))).lstrip("[").rstrip("]")
            name = f"{repr(self.origin)}.{self.function_name}({formatted_parameters})"
        else:
            name = f"Regular transfer to {self.address}"

        return name if self.extra is None else name + f" with {self.extra}"

    def estimated_gas(self, from_address: Address) -> int:
        """Return an estimated amount of gas which will get consumed by this Ethereum transaction.

        May throw an exception if the actual transaction will fail as well.

        Args:
            from_address: Address to simulate sending the transaction from.

        Returns:
            Amount of gas as an integer.
        """
        assert(isinstance(from_address, Address))

        if self.contract is not None:
            if self.function_name is None:
                return self.web3.eth.estimateGas({**self._as_dict(self.extra), **{'from': from_address.address,
                                                                                  'to': self.address.address,
                                                                                  'data': self.parameters[0]}})

            else:
                estimate = self._contract_function() \
                        .estimateGas({**self._as_dict(self.extra), **{'from': from_address.address}})

        else:
            estimate = 21000

        return estimate

    def transact(self, **kwargs) -> Optional[Receipt]:
        """Executes the Ethereum transaction synchronously.

        Executes the Ethereum transaction synchronously. The method will block until the
        transaction gets mined i.e. it will return when either the transaction execution
        succeeded or failed. In case of the former, a :py:class:`pymaker.Receipt`
        object will be returned.

        Out-of-gas exceptions are automatically recognized as transaction failures.

        Allowed keyword arguments are: `from_address`, `replace`, `gas`, `gas_buffer`, `gas_price`.
        `gas_price` needs to be an instance of a class inheriting from :py:class:`pymaker.gas.GasPrice`.
        `from_address` needs to be an instance of :py:class:`pymaker.Address`.

        The `gas` keyword argument is the gas limit for the transaction, whereas `gas_buffer`
        specifies how much gas should be added to the estimate. They can not be present
        at the same time. If none of them are present, a default buffer is added to the estimate.

        Returns:
            A :py:class:`pymaker.Receipt` object if the transaction invocation was successful.
            `None` otherwise.
        """
        return synchronize([self.transact_async(**kwargs)])[0]

    @_track_status
    async def transact_async(self, **kwargs) -> Optional[Receipt]:
        """Executes the Ethereum transaction asynchronously.

        Executes the Ethereum transaction asynchronously. The method will return immediately.
        Ultimately, its future value will become either a :py:class:`pymaker.Receipt` or `None`,
        depending on whether the transaction execution was successful or not.

        Out-of-gas exceptions are automatically recognized as transaction failures.

        Allowed keyword arguments are: `from_address`, `replace`, `gas`, `gas_buffer`, `gas_price`.
        `gas_price` needs to be an instance of a class inheriting from :py:class:`pymaker.gas.GasPrice`.

        The `gas` keyword argument is the gas limit for the transaction, whereas `gas_buffer`
        specifies how much gas should be added to the estimate. They can not be present
        at the same time. If none of them are present, a default buffer is added to the estimate.

        Returns:
            A future value of either a :py:class:`pymaker.Receipt` object if the transaction
            invocation was successful, or `None` if it failed.
        """

        unknown_kwargs = set(kwargs.keys()) - {'from_address', 'replace', 'gas', 'gas_buffer', 'gas_price'}
        if len(unknown_kwargs) > 0:
            raise Exception(f"Unknown kwargs: {unknown_kwargs}")

        # Get the from account.
        from_account = kwargs['from_address'].address if ('from_address' in kwargs) else self.web3.eth.defaultAccount

        # First we try to estimate the gas usage of the transaction. If gas estimation fails
        # it means there is no point in sending the transaction, thus we fail instantly and
        # do not increment the nonce. If the estimation is successful, we pass the calculated
        # gas value (plus some `gas_buffer`) to the subsequent `transact` calls so it does not
        # try to estimate it again.
        try:
            gas_estimate = self.estimated_gas(Address(from_account))
        except:
            self.logger.warning(f"Transaction {self.name()} will fail, refusing to send ({sys.exc_info()[1]})")
            return None

        # Get or calculate `gas`. Get `gas_price`, which in fact refers to a gas pricing algorithm.
        gas = self._gas(gas_estimate, **kwargs)
        gas_price = kwargs['gas_price'] if ('gas_price' in kwargs) else DefaultGasPrice()
        assert(isinstance(gas_price, GasPrice))

        # Get the transaction this one is supposed to replace.
        # If there is one, try to borrow the nonce from it as long as that transaction isn't finished.
        replaced_tx = kwargs['replace'] if ('replace' in kwargs) else None
        if replaced_tx is not None:
            while replaced_tx.nonce is None and replaced_tx.status != TransactStatus.FINISHED:
                await asyncio.sleep(0.25)

            self.nonce = replaced_tx.nonce

        # Initialize variables which will be used in the main loop.
        tx_hashes = []
        initial_time = time.time()
        gas_price_last = 0

        while True:
            seconds_elapsed = int(time.time() - initial_time)

            if self.nonce is not None and self.web3.eth.getTransactionCount(from_account) > self.nonce:
                # Check if any transaction sent so far has been mined (has a receipt).
                # If it has, we return either the receipt (if if was successful) or `None`.
                for attempt in range(1, 11):
                    for tx_hash in tx_hashes:
                        receipt = self._get_receipt(tx_hash)
                        if receipt:
                            if receipt.successful:
                                self.logger.info(f"Transaction {self.name()} was successful (tx_hash={bytes_to_hexstring(tx_hash)})")
                                return receipt
                            else:
                                self.logger.warning(f"Transaction {self.name()} mined successfully but generated no single"
                                                    f" log entry, assuming it has failed (tx_hash={bytes_to_hexstring(tx_hash)})")
                                return None

                    self.logger.debug(f"No receipt found in attempt #{attempt}/10 (nonce={self.nonce},"
                                      f" getTransactionCount={self.web3.eth.getTransactionCount(from_account)})")

                    await asyncio.sleep(0.5)

                # If we can not find a mined receipt but at the same time we know last used nonce
                # has increased, then it means that the transaction we tried to send failed.
                self.logger.warning(f"Transaction {self.name()} has been overridden by another transaction"
                                    f" with the same nonce, which means it has failed")
                return None

            # Send a transaction if:
            # - no transaction has been sent yet, or
            # - the gas price requested has changed since the last transaction has been sent
            gas_price_value = gas_price.get_gas_price(seconds_elapsed)
            if len(tx_hashes) == 0 or ((gas_price_value is not None) and (gas_price_last is not None) and
                                           (gas_price_value > gas_price_last * 1.1)):
                gas_price_last = gas_price_value

                try:
                    # We need the lock in order to not try to send two transactions with the same nonce.
                    with transaction_lock:
                        if self.nonce is None:
                            if self._is_parity():
                                self.nonce = int(self.web3.manager.request_blocking("parity_nextNonce", [from_account]), 16)

                            else:
                                self.nonce = self.web3.eth.getTransactionCount(from_account, block_identifier='pending')

                        tx_hash = self._func(from_account, gas, gas_price_value, self.nonce)
                        tx_hashes.append(tx_hash)

                    self.logger.info(f"Sent transaction {self.name()} with nonce={self.nonce}, gas={gas},"
                                     f" gas_price={gas_price_value if gas_price_value is not None else 'default'}"
                                     f" (tx_hash={bytes_to_hexstring(tx_hash)})")
                except Exception as e:
                    self.logger.warning(f"Failed to send transaction {self.name()} with nonce={self.nonce}, gas={gas},"
                                        f" gas_price={gas_price_value if gas_price_value is not None else 'default'}"
                                        f" ({e})")

                    if len(tx_hashes) == 0:
                        raise

            await asyncio.sleep(0.25)

    def invocation(self) -> Invocation:
        """Returns the `Invocation` object for this pending Ethereum transaction.

        The :py:class:`pymaker.Invocation` object may be used with :py:class:`pymaker.transactional.TxManager`
        to invoke multiple contract calls in one Ethereum transaction.

        Please see :py:class:`pymaker.transactional.TxManager` documentation for more details.

        Returns:
            :py:class:`pymaker.Invocation` object for this pending Ethereum transaction.
        """
        return Invocation(self.address, Calldata(self._contract_function()._encode_transaction_data()))


class Transfer:
    """Represents an ERC20 token transfer.

    Represents an ERC20 token transfer resulting from contract method execution.
    A list of transfers can be found in the :py:class:`pymaker.Receipt` class.

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

    def __eq__(self, other):
        assert(isinstance(other, Transfer))
        return self.token_address == other.token_address and \
               self.from_address == other.from_address and \
               self.to_address == other.to_address and \
               self.value == other.value

    def __hash__(self):
        return hash((self.token_address, self.from_address, self.token_address, self.value))


def eth_transfer(web3: Web3, to: Address, amount: Wad) -> Transact:
    return Transact(None, web3, None, to, None, None, None, {'value': amount.value})
