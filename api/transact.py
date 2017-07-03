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
from typing import Optional

from web3 import Web3

from api import Contract, Address, Receipt


class TransactionManager(Contract):
    """A client for the `TransactionManager` contract.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `TransactionManager` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/TransactionManager.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def execute(self, tokens: list, invocations: list) -> Optional[Receipt]:
        def token_addresses() -> list:
            return list(map(lambda address: address.address, tokens))

        def script() -> bytes:
            return reduce(operator.add, map(lambda invocation: script_entry(invocation), invocations), bytes())

        def script_entry(invocation: dict) -> bytes:
            body = bytes.fromhex(invocation['address'].address.replace('0x', '')) + bytes.fromhex(invocation['calldata'].replace('0x', ''))
            header = len(body).to_bytes(32, byteorder='big')
            return header + body

        try:
            tx_hash = self._contract.transact().execute(token_addresses(), script())
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None
