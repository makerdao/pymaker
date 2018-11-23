# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2018 bargst
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
from typing import List

from hexbytes import HexBytes
from web3 import Web3
from web3.utils.events import get_event_data

from pymaker import Address, Contract, Transact, Receipt, Calldata
from pymaker.util import hexstring_to_bytes


class DSProxyCache(Contract):
    """A client for the `DSProxyCache` contract.

    Ref. <https://github.com/dapphub/ds-proxy/blob/master/src/proxy.sol#L120>
    """

    abi = Contract._load_abi(__name__, 'abi/DSProxyCache.abi')
    bin = Contract._load_bin(__name__, 'abi/DSProxyCache.bin')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @classmethod
    def deploy(cls, web3: Web3):
        return cls(web3=web3, address=Contract._deploy(web3, cls.abi, cls.bin, []))

    def read(self, code: str) -> Address:
        assert (isinstance(code, str))

        b32_code = hexstring_to_bytes(code)
        address = self._contract.call().read(b32_code)

        return Address(address)

    def write(self, code: str):
        assert (isinstance(code, str))

        b32_code = hexstring_to_bytes(code)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'write', [b32_code])


class DSProxy(Contract):
    """A client for the `DSProxy` contract.

    Ref. <https://github.com/dapphub/ds-proxy/blob/master/src/proxy.sol#L28>
    """

    abi = Contract._load_abi(__name__, 'abi/DSProxy.abi')
    bin = Contract._load_bin(__name__, 'abi/DSProxy.bin')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @classmethod
    def deploy(cls, web3: Web3, cache: Address):
        return cls(web3=web3, address=Contract._deploy(web3, cls.abi, cls.bin, [cache.address]))

    def execute(self, code: str, calldata: Calldata) -> Transact:
        assert (isinstance(code, str))
        assert (isinstance(calldata, Calldata))

        b32_code = hexstring_to_bytes(code)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'execute(bytes,bytes)', [b32_code, calldata.as_bytes()])

    def execute_at(self, address: Address, calldata: Calldata) -> Transact:
        assert (isinstance(address, Address))
        assert (isinstance(calldata, Calldata))

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'execute(address,bytes)', [address.address, calldata.as_bytes()])

    def set_cache(self, address: Address) -> Transact:
        assert (isinstance(address, Address))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'setCache', [address.address])

    def cache(self) -> Address:
        return Address(self._contract.call().cache())


# event Created(address indexed sender, address indexed owner, address proxy, address cache);
class LogCreated:
    def __init__(self, log):
        self.sender = Address(log['args']['sender'])
        self.owner = Address(log['args']['owner'])
        self.proxy = Address(log['args']['proxy'])
        self.cache = Address(log['args']['cache'])
        self.raw = log

    @classmethod
    def from_event(cls, event: dict):
        assert (isinstance(event, dict))

        topics = event.get('topics')
        if topics and topics[0] == HexBytes('0x259b30ca39885c6d801a0b5dbc988640f3c25e2f37531fe138c5c5af8955d41b'):
            log_created_abi = [abi for abi in DSProxyFactory.abi if abi.get('name') == 'Created'][0]
            event_data = get_event_data(log_created_abi, event)

            return LogCreated(event_data)
        else:
            raise Exception(f'[from_event] Invalid topic in {event}')

    def __eq__(self, other):
        assert (isinstance(other, LogCreated))
        return self.__dict__ == other.__dict__


class DSProxyFactory(Contract):
    """A client for the `DSProxyFactory` contract.

    Ref. <https://github.com/dapphub/ds-proxy/blob/master/src/proxy.sol#L90>
    """

    abi = Contract._load_abi(__name__, 'abi/DSProxyFactory.abi')
    bin = Contract._load_bin(__name__, 'abi/DSProxyFactory.bin')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @classmethod
    def deploy(cls, web3: Web3):
        return cls(web3=web3, address=Contract._deploy(web3, cls.abi, cls.bin, []))

    def build(self) -> Transact:
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'build()', [])

    def build_for(self, address: Address) -> Transact:
        assert (isinstance(address, Address))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'build(address)', [address.address])

    def cache(self) -> Address:
        return Address(self._contract.call().cache())

    def is_proxy(self, address: Address) -> bool:
        assert (isinstance(address, Address))

        return self._contract.call().isProxy(address.address)

    def past_build(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogCreated]:
        """Synchronously retrieve past LogCreated events.

        `LogCreated` events are emitted every time someone build a proxy from the factory.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `LogCreated` events represented as :py:class:`pymaker.proxy.LogCreated` class.
        """
        assert isinstance(number_of_past_blocks, int)
        assert isinstance(event_filter, dict) or (event_filter is None)

        return self._past_events(self._contract, 'Created', LogCreated, number_of_past_blocks, event_filter)

    @classmethod
    def log_created(cls, receipt: Receipt) -> List[LogCreated]:
        assert isinstance(receipt, Receipt)

        events = []
        for log in receipt.raw_receipt.logs:
            try:
                event = LogCreated.from_event(dict(log))
                events.append(event)
            except:
                pass
        return events
