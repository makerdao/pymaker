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

import operator
from functools import reduce
from typing import Optional, List

from web3 import Web3

from api import Contract, Address, Receipt, Calldata
from api.token import ERC20Token


class Invocation(object):
    """Single smart contract method invocation, to be used together with `TxManager`.

    Attributes:
        address: Smart contract address.
        calldata: The calldata of the invocation.
    """
    def __init__(self, address: Address, calldata: Calldata):
        assert(isinstance(address, Address))
        assert(isinstance(calldata, Calldata))
        self.address = address
        self.calldata = calldata


class TxManager(Contract):
    """A client for the `TxManager` contract.

    `TxManager` allows to invoke multiple smart contract methods in one Ethereum transaction.
    Each invocation is represented as an instance of the `Invocation` class, containing a
    contract address and a calldata.

    In addition to that, these invocations can use ERC20 token balances. In order to do that,
    the entire allowance of each token involved is transferred from the caller to the `TxManager`
    contract at the beginning of the transaction and all the remaining balances are returned
    to the caller at the end of it. In order to use this feature, ERC20 token allowances
    have to be granted to the `TxManager`.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `TxManager` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/TxManager.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def approve(self, tokens: List[ERC20Token], approval_function):
        for token in tokens:
            approval_function(token, self.address, 'TxManager')

    def owner(self) -> Address:
        return Address(self._contract.call().owner())

    def execute(self, tokens: List[Address], invocations: List[Invocation]) -> Optional[Receipt]:
        """Executes multiple smart contract methods in one Ethereum transaction.

        Args:
            tokens: List of addresses of ERC20 token the invocations should be able to access.
            invocations: A list of invocations (smart contract methods) to be executed.
        """
        def token_addresses() -> list:
            return list(map(lambda address: address.address, tokens))

        def script() -> bytes:
            return reduce(operator.add, map(lambda invocation: script_entry(invocation), invocations), bytes())

        def script_entry(invocation: Invocation) -> bytes:
            body = invocation.address.as_bytes() + invocation.calldata.as_bytes()
            header = len(body).to_bytes(32, byteorder='big')
            return header + body

        assert(isinstance(tokens, list))
        assert(isinstance(invocations, list))

        return self._transact(self.web3, f"TxManager('{self.address}').execute('0x...', '0x....')",
                              lambda: self._contract.transact().execute(token_addresses(), script()))
