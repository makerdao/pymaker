# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019 EdNoepel
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

import datetime
from web3 import Web3
from typing import List
from pprint import pformat

from pymaker import Contract, Address, Transact, Wad
from pymaker.auth import DSAuth
from pymaker.token import DSToken


# TODO: Complete implementation and unit test
class DSPause(Contract):
    """A client for the `DSPause` contract, which schedules function calls after a predefined delay.

    You can find the source code of the `DSPause` contract here:
    <https://github.com/dapphub/ds-pause>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSPause` contract.
    """

    class Plan:
        def __init__(self, usr: Address, fax: bytes, eta: datetime):
            """Creates a plan to be executed later.

            Args:
            usr: Address of the caller
            fax: Identifies the calldata
            eta: Identifies the earliest time of execution
            """
            assert isinstance(usr, Address)
            assert isinstance(fax, bytes)
            assert isinstance(eta, datetime.datetime)

            self.usr = usr
            self.fax = fax
            self.eta = eta.timestamp()

    abi = Contract._load_abi(__name__, 'abi/DSPause.abi')
    bin = Contract._load_bin(__name__, 'abi/DSPause.bin')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3, delay: int, owner: Address, ds_auth: DSAuth):
        return DSPause(web3=web3, address=Contract._deploy(web3, DSPause.abi, DSPause.bin,
                                                           [delay, owner.address, ds_auth.address.address]))

    # TODO: Awaiting updated ABI/BIN from dss-deploy
    # def plot(self, plan: Plan):
    #     return self._transact(plan, "plot")

    def drop(self, plan: Plan):
        return self._transact(plan, "drop")

    def exec(self, plan: Plan) -> Transact:
        return self._transact(plan, "exec")

    def _transact(self, plan: Plan, function_name: str) -> Transact:
        assert isinstance(plan, DSPause.Plan)
        assert isinstance(function_name, str)

        return Transact(self, self.web3, self.abi, self.address, self._contract, function_name,
                        [plan.usr.address, plan.fax, int(plan.eta)])


# TODO: Implement and unit test
class DSRoles(Contract):
    """A client for the `DSRoles` contract, which manages lists of user roles and capabilities.

    You can find the source code of the `DSRoles` contract here:
    <https://github.com/dapphub/ds-roles>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSRoles` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSRoles.abi')
    bin = Contract._load_bin(__name__, 'abi/DSRoles.bin')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def is_root_user(self, who: Address) -> bool:
        assert isinstance(who, Address)

        return bool(self._contract.call().isUserRoot(who.address))

    def set_root_user(self, who: Address, enabled=True) -> Transact:
        assert isinstance(who, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        "setRootUser", [who.address, enabled])

    def has_user_role(self, who: Address, role: int) -> bool:
        assert isinstance(who, Address)
        assert isinstance(role, int)
        assert 0 <= role <= int('0xFFFFFFFF')

        return bool(self._contract.call().hasUserRole(who.address, role))

    def set_user_role(self, who: Address, role: int, enabled=True) -> Transact:
        assert isinstance(who, Address)
        assert isinstance(role, int)
        assert 0 <= role <= int('0xFFFFFFFF')

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        "setUserRole", [who.address, role, enabled])


class Etch:
    def __init__(self, log):
        self.slate = log['args']['slate']
        self.address = log['address']
        self.block_number = log['blockNumber']
        self.log_index = log['logIndex']
        self.tx_hash = log['transactionHash']

    def __repr__(self):
        return pformat(vars(self))


class DSChief(Contract):
    """A client for the `DSChief` contract, which manages lists of user roles and capabilities.

    You can find the source code of the `DSChief` contract here:
    <https://github.com/dapphub/ds-chief>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSChief` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSChief.abi')
    bin = Contract._load_bin(__name__, 'abi/DSChief.bin')

    def __init__(self, web3: Web3, address: Address):
        assert (isinstance(web3, Web3))
        assert (isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def get_votes(self, address):
        return self._contract.call().votes(address)

    def get_yay(self, slate, position) -> str:
        return self._contract.call().slates(slate, position)

    def get_deposits(self, address) -> Wad:
        return Wad(self._contract.call().deposits(address))

    def get_approvals(self, address) -> Wad:
        return Wad(self._contract.call().approvals(address))

    def get_hat(self) -> Address:
        return Address(self._contract.call().hat())

    def get_max_yays(self) -> int:
        return self._contract.call().MAX_YAYS()

    def lock(self, amount: Wad) -> Transact:
        assert isinstance(amount, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'lock', [amount.value])

    def free(self, amount: Wad) -> Transact:
        assert isinstance(amount, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'free', [amount.value])

    def etch(self, yays: List) -> Transact:
        assert isinstance(yays, List)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'etch(address[])', [yays])

    def vote_yays(self, yays: List) -> Transact:
        assert isinstance(yays, List)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'vote(address[])', [yays])

    def vote_etch(self, etch: Etch) -> Transact:
        assert isinstance(etch, Etch)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'vote(bytes32)', [etch.slate])

    def lift(self, whom: Address) -> Transact:
        assert isinstance(whom, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'lift', [whom.address])

    def past_etch(self, number_of_past_blocks: int, event_filter: dict = None) -> List[Etch]:
        """Synchronously retrieve past Etch events.

        `Etch` events are emitted by the ds-chief contract every time someone places a vote.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `Etch` events represented as :py:class:`pymaker.governance.Etch` class.
        """
        assert(isinstance(number_of_past_blocks, int))
        assert(isinstance(event_filter, dict) or (event_filter is None))

        return self._past_events(self._contract, 'Etch', Etch, number_of_past_blocks, event_filter)

    def past_etch_in_range(self, from_block: int, to_block: int, event_filter: dict = None) -> List[Etch]:
        """Synchronously retrieve past Etch events.

        `Etch` events are emitted by the ds-chief contract every time someone places a vote.

        Args:
            from_block: Starting block to retrieve the events from.
            to_block: Last block to retrieve the events to.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `Etch` events represented as :py:class:`pymaker.governance.Etch` class.
        """
        assert(isinstance(from_block, int))
        assert(isinstance(to_block, int))
        assert(isinstance(event_filter, dict) or (event_filter is None))

        return self._past_events_in_block_range(self._contract, 'Etch', Etch, from_block, to_block, event_filter)
