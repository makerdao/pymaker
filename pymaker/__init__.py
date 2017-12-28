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
import time
from functools import total_ordering
from typing import Optional

import eth_utils
import pkg_resources
from web3 import Web3
from web3.utils.events import get_event_data

from pymaker.gas import DefaultGasPrice, GasPrice
from pymaker.numeric import Wad
from pymaker.util import synchronize

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
    logger = logging.getLogger('contract')

    @staticmethod
    def _deploy(web3: Web3, abi: list, bytecode: bytes, args: list) -> Address:
        assert(isinstance(web3, Web3))
        assert(isinstance(abi, list))
        assert(isinstance(bytecode, bytes))
        assert(isinstance(args, list))

        tx_hash = web3.eth.contract(abi=abi, bytecode=bytecode).deploy(args=args)
        receipt = web3.eth.getTransactionReceipt(tx_hash)
        return Address(receipt['contractAddress'])

    @staticmethod
    def _get_contract(web3: Web3, abi: list, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(abi, list))
        assert(isinstance(address, Address))

        code = web3.eth.getCode(address.address)
        if (code == "0x") or (code is None):
            raise Exception(f"No contract found at {address}")

        return web3.eth.contract(abi=abi)(address=address.address)

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
            handler(cls(log))
        return callback

    @staticmethod
    def _load_abi(package, resource) -> list:
        return json.loads(pkg_resources.resource_string(package, resource))

    @staticmethod
    def _load_bin(package, resource) -> bytes:
        return pkg_resources.resource_string(package, resource)


class Calldata:
    """Represents Ethereum calldata.

    Attributes:
        value: Calldata as a string starting with `0x`.
    """
    def __init__(self, value: str):
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
    """Represents a receipt for an Ethereum transaction.

    Attributes:
        raw_receipt: Raw receipt received from the Ethereum node.
        transaction_hash: Hash of the Ethereum transaction.
        gas_used: Amount of gas used by the Ethereum transaction.
        transfers: A list of ERC20 token transfers resulting from the execution
            of this Ethereum transaction. Each transfer is an instance of the
            :py:class:`pymaker.Transfer` class.
        successful: Boolean flag which is `True` if the Ethereum transaction
            was successful. We consider transaction successful if the contract
            method has been executed without throwing.
    """
    def __init__(self, receipt):
        self.raw_receipt = receipt
        self.transaction_hash = receipt['transactionHash']
        self.gas_used = receipt['gasUsed']
        self.transfers = []

        receipt_logs = receipt['logs']
        if (receipt_logs is not None) and (len(receipt_logs) > 0):
            self.successful = True
            for receipt_log in receipt_logs:
                if len(receipt_log['topics']) > 0 and receipt_log['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                    from pymaker.token import ERC20Token
                    transfer_abi = [abi for abi in ERC20Token.abi if abi.get('name') == 'Transfer'][0]
                    event_data = get_event_data(transfer_abi, receipt_log)
                    self.transfers.append(Transfer(token_address=Address(event_data['address']),
                                                   from_address=Address(event_data['args']['from']),
                                                   to_address=Address(event_data['args']['to']),
                                                   value=Wad(event_data['args']['value'])))
        else:
            self.successful = False


class Transact:
    """Represents an Ethereum transaction before it gets executed."""

    logger = logging.getLogger('transact')

    def __init__(self,
                 origin: object,
                 web3: Web3,
                 abi: list,
                 address: Address,
                 contract: object,
                 function_name: str,
                 parameters: list,
                 extra: Optional[dict] = None):
        assert(isinstance(origin, object))
        assert(isinstance(web3, Web3))
        assert(isinstance(abi, list))
        assert(isinstance(address, Address))
        assert(isinstance(contract, object))
        assert(isinstance(function_name, str))
        assert(isinstance(parameters, list))
        assert(isinstance(extra, dict) or (extra is None))

        self.origin = origin
        self.web3 = web3
        self.abi = abi
        self.address = address
        self.contract = contract
        self.function_name = function_name
        self.parameters = parameters
        self.extra = extra

    def _get_receipt(self, transaction_hash: str) -> Optional[Receipt]:
        receipt = self.web3.eth.getTransactionReceipt(transaction_hash)
        if receipt is not None and receipt['blockNumber'] is not None:
            return Receipt(receipt)
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

    def _func(self, gas: int, gas_price: Optional[int], nonce: Optional[int]):
        gas_price_dict = {'gasPrice': gas_price} if gas_price is not None else {}
        nonce_dict = {'nonce': nonce} if nonce is not None else {}

        return self.contract.\
            transact({**{'gas': gas}, **gas_price_dict, **nonce_dict, **self._as_dict(self.extra)}).\
            __getattr__(self.function_name)(*self.parameters)

    def name(self) -> str:
        """Returns the nicely formatted name of this pending Ethereum transaction.

        Returns:
            Nicely formatted name of this pending Ethereum transaction.
        """
        name = f"{repr(self.origin)}.{self.function_name}({self.parameters})"
        return name if self.extra is None else name + f" with {self.extra}"

    def estimated_gas(self) -> int:
        """Return an estimated amount of gas which will get consumed by this Ethereum transaction.

        May throw an exception if the actual transaction will fail as well.

        Returns:
            Amount of gas as an integer.
        """
        estimate = self.contract.estimateGas(self._as_dict(self.extra)).__getattr__(self.function_name)(*self.parameters)

        # testrpc does estimate too little gas at times, it did happen with TxManager definitely
        # so we always add 1mio tp the estimate as in testrpc gas block limit doesn't matter
        if str(self.web3.providers[0]) == 'EthereumTesterProvider':
            estimate = estimate + 1000000

        return estimate

    def transact(self, **kwargs) -> Optional[Receipt]:
        """Executes the Ethereum transaction synchronously.

        Executes the Ethereum transaction synchronously. The method will block until the
        transaction gets mined i.e. it will return when either the transaction execution
        succeeded or failed. In case of the former, a :py:class:`pymaker.Receipt`
        object will be returned.

        Out-of-gas exceptions are automatically recognized as transaction failures.

        Allowed keyword arguments are: `gas`, `gas_buffer`, `gas_price`. `gas_price` needs
        to be an instance of a class inheriting from :py:class:`pymaker.gas.GasPrice`.

        The `gas` keyword argument is the gas limit for the transaction, whereas `gas_buffer`
        specifies how much gas should be added to the estimate. They can not be present
        at the same time. If none of them are present, a default buffer is added to the estimate.

        Returns:
            A :py:class:`pymaker.Receipt` object if the transaction invocation was successful.
            `None` otherwise.
        """
        return synchronize([self.transact_async(**kwargs)])[0]

    async def transact_async(self, **kwargs) -> Optional[Receipt]:
        """Executes the Ethereum transaction asynchronously.

        Executes the Ethereum transaction asynchronously. The method will return immediately.
        Ultimately, its future value will become either a :py:class:`pymaker.Receipt` or `None`,
        depending on whether the transaction execution was successful or not.

        Out-of-gas exceptions are automatically recognized as transaction failures.

        Allowed keyword arguments are: `gas`, `gas_buffer`, `gas_price`. `gas_price` needs
        to be an instance of a class inheriting from :py:class:`pymaker.gas.GasPrice`.

        The `gas` keyword argument is the gas limit for the transaction, whereas `gas_buffer`
        specifies how much gas should be added to the estimate. They can not be present
        at the same time. If none of them are present, a default buffer is added to the estimate.

        Returns:
            A future value of either a :py:class:`pymaker.Receipt` object if the transaction
            invocation was successful, or `None` if it failed.
        """
        # First we try to estimate the gas usage of the transaction. If gas estimation fails
        # it means there is no point in sending the transaction, thus we fail instantly and
        # do not increment the nonce. If the estimation is successful, we pass the calculated
        # gas value (plus some `gas_buffer`) to the subsequent `transact` calls so it does not
        # try to estimate it again. If it would try to estimate it again it could turn out
        # this transaction will fail (another block might have been mined in the meantime for
        # example), which would mean we incremented the nonce but never used it.
        #
        # This is why gas estimation has to happen first and before the nonce gets incremented.
        try:
            gas_estimate = self.estimated_gas()
        except:
            self.logger.warning(f"Transaction {self.name()} will fail, refusing to send ({sys.exc_info()[1]})")
            return None

        # Get or calculate `gas`. Get `gas_price`, which in fact refers to a gas pricing algorithm.
        gas = self._gas(gas_estimate, **kwargs)
        gas_price = kwargs['gas_price'] if ('gas_price' in kwargs) else DefaultGasPrice()
        assert(isinstance(gas_price, GasPrice))

        # Initialize variables which will be used in the main loop.
        nonce = None
        tx_hashes = []
        initial_time = time.time()
        gas_price_last = 0

        while True:
            seconds_elapsed = int(time.time() - initial_time)

            if nonce and self.web3.eth.getTransactionCount(self.web3.eth.defaultAccount) > nonce:
                # Check if any transaction sent so far has been mined (has a receipt).
                # If it has, we return either the receipt (if if was successful) or `None`.
                for tx_hash in tx_hashes:
                    receipt = self._get_receipt(tx_hash)
                    if receipt:
                        if receipt.successful:
                            self.logger.info(f"Transaction {self.name()} was successful (tx_hash={tx_hash})")
                            return receipt
                        else:
                            self.logger.warning(f"Transaction {self.name()} mined successfully but generated no single"
                                                f" log entry, assuming it has failed (tx_hash={tx_hash})")
                            return None

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
                                           (gas_price_value > gas_price_last)):
                gas_price_last = gas_price_value

                try:
                    tx_hash = self._func(gas, gas_price_value, nonce)
                    tx_hashes.append(tx_hash)

                    # If this is the first transaction sent, get its nonce so we can override the transaction with
                    # another one using higher gas price if :py:class:`pymaker.gas.GasPrice` tells us to do so
                    if nonce is None:
                        nonce = self.web3.eth.getTransaction(tx_hash)['nonce']

                    self.logger.info(f"Sent transaction {self.name()} with nonce={nonce}, gas={gas},"
                                     f" gas_price={gas_price_value if gas_price_value is not None else 'default'}"
                                     f" (tx_hash={tx_hash})")
                except:
                    self.logger.warning(f"Failed to send transaction {self.name()} with nonce={nonce}, gas={gas},"
                                        f" gas_price={gas_price_value if gas_price_value is not None else 'default'}")

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
        return Invocation(self.address,
                          Calldata(self.web3.eth.contract(abi=self.abi).encodeABI(self.function_name, self.parameters)))


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
