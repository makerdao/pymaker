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

from web3 import Web3

from api import Contract, Address, Transact


class DSProxy(Contract):
    """A client for the `DSProxy` contract.

    You can find the source code of the `DSProxy` contract here:
    <https://github.com/dapphub/ds-proxy>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSProxy` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSProxy.abi')
    bin = Contract._load_bin(__name__, 'abi/DSProxy.bin')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def execute(self, contract: bytes, calldata: bytes) -> Transact:
        """Create a new contract and call a function of it.

        Creates a new contract using the bytecode (`contract`). Then does _delegatecall_ to the function
        and arguments specified in the `calldata`.

        Args:
            contract: Contract bytecode.
            calldata: Calldata to pass to _delegatecall_.
        """
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'execute', [contract, calldata])

    def __repr__(self):
        return f"DSProxy('{self.address}')"
