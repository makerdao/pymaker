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

from pymaker import Contract, Address, Transact
from pymaker.auth import DSAuth


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

