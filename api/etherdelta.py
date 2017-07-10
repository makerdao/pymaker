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

from pprint import pformat
from typing import Optional, List

from web3 import Web3

from api import Contract, Address, Receipt, Calldata
from api.numeric import Wad
from api.token import ERC20Token
from api.util import int_to_bytes32, bytes_to_int


class EtherDelta(Contract):
    """A client for the EtherDelta exchange contract.

    You can find the source code of the `EtherDelta` contract here:
    <https://etherscan.io/address/0x8d12a197cb00d4747a1fe03395095ce2a5cc6819#code>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `EtherDelta` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/EtherDelta.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def approve(self, tokens: List[ERC20Token], approval_function):
        for token in tokens:
            approval_function(token, self.address, 'EtherDelta')

    def admin(self) -> Address:
        return Address(self._contract.call().admin())

    def fee_account(self) -> Address:
        return Address(self._contract.call().feeAccount())

    def fee_make(self) -> Wad:
        return Wad(self._contract.call().feeMake())

    def fee_take(self) -> Wad:
        return Wad(self._contract.call().feeTake())

    def fee_rebate(self) -> Wad:
        return Wad(self._contract.call().feeRebate())

    def deposit(self, amount: Wad) -> Optional[Receipt]:
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"EtherDelta('{self.address}').deposit() with value='{amount}'",
                              lambda: self._contract.transact({'value': amount.value}).deposit())

    def withdraw(self, amount: Wad) -> Optional[Receipt]:
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"EtherDelta('{self.address}').withdraw('{amount}')",
                              lambda: self._contract.transact().withdraw(amount.value))

    def balance_of(self, user: Address) -> Wad:
        assert(isinstance(user, Address))
        return Wad(self._contract.call().balanceOf('0x0000000000000000000000000000000000000000', user.address))

    def deposit_token(self, token: Address, amount: Wad) -> Optional[Receipt]:
        assert(isinstance(token, Address))
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"EtherDelta('{self.address}').depositToken('{token}', '{amount}')",
                              lambda: self._contract.transact().depositToken(token.address, amount.value))

    def withdraw_token(self, token: Address, amount: Wad) -> Optional[Receipt]:
        assert(isinstance(token, Address))
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"EtherDelta('{self.address}').withdrawToken('{token}', '{amount}')",
                              lambda: self._contract.transact().withdrawToken(token.address, amount.value))

    def balance_of_token(self, token: Address, user: Address) -> Wad:
        assert(isinstance(token, Address))
        assert(isinstance(user, Address))
        return Wad(self._contract.call().balanceOf(token.address, user.address))
