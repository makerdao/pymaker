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

import operator
from functools import reduce
from typing import List

from web3 import Web3

from pymaker import Contract, Address, Invocation, Transact
from pymaker.token import ERC20Token


class TxManager(Contract):
    """A client for the `TxManager` contract.

    `TxManager` allows to invoke multiple contract methods in one Ethereum transaction.
    Each invocation is represented as an instance of the `Invocation` class, containing a
    contract address and a calldata.

    In addition to that, these invocations can use ERC20 token balances. In order to do that,
    the entire allowance of each token involved is transferred from the caller to the `TxManager`
    contract at the beginning of the transaction and all the remaining balances are returned
    to the caller at the end of it. In order to use this feature, ERC20 token allowances
    have to be granted to the `TxManager`.

    You can find the source code of the `TxManager` contract here:
    <https://github.com/makerdao/tx-manager>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `TxManager` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/TxManager.abi')
    bin = Contract._load_bin(__name__, 'abi/TxManager.bin')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3):
        return TxManager(web3=web3, address=Contract._deploy(web3, TxManager.abi, TxManager.bin, []))

    def approve(self, tokens: List[ERC20Token], approval_function):
        """Approve the TxManager contract to fully access balances of specified tokens.

        For available approval functions (i.e. approval modes) see `directly` and `via_tx_manager`
        in `pymaker.approval`.

        Args:
            tokens: List of :py:class:`pymaker.token.ERC20Token` class instances.
            approval_function: Approval function (i.e. approval mode).
        """
        assert(isinstance(tokens, list))
        assert(callable(approval_function))

        for token in tokens:
            approval_function(token, self.address, 'TxManager')

    def owner(self) -> Address:
        return Address(self._contract.call().owner())

    def execute(self, tokens: List[Address], invocations: List[Invocation]) -> Transact:
        """Executes multiple contract methods in one Ethereum transaction.

        Args:
            tokens: List of addresses of ERC20 token the invocations should be able to access.
            invocations: A list of invocations (contract methods) to be executed.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        def token_addresses() -> list:
            return list(map(lambda address: address.address, tokens))

        def script() -> bytes:
            return reduce(operator.add, map(lambda invocation: script_entry(invocation), invocations), bytes())

        def script_entry(invocation: Invocation) -> bytes:
            address = invocation.address.as_bytes()
            calldata = invocation.calldata.as_bytes()
            calldata_length = len(calldata).to_bytes(32, byteorder='big')
            return address + calldata_length + calldata

        assert(isinstance(tokens, list))
        assert(isinstance(invocations, list))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'execute', [token_addresses(), script()])

    def __repr__(self):
        return f"TxManager('{self.address}')"
