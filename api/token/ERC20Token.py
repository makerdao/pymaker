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

from typing import Optional

from api.Address import Address
from api.Contract import Contract
from api.Receipt import Receipt
from api.Wad import Wad


class ERC20Token(Contract):
    """A client for a standard ERC20 token contract.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the ERC20 token.
    """

    abi = Contract._load_abi(__name__, 'ERC20Token.abi')
    registry = {}

    def __init__(self, web3, address):
        self.web3 = web3
        self.address = address
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def name(self):
        return ERC20Token.registry.get(self.address, '???')

    def total_supply(self) -> Wad:
        """Returns the total supply of the token.
        
        Returns:
            The total supply of the token.
        """
        return Wad(self._contract.call().totalSupply())

    def balance_of(self, address: Address) -> Wad:
        """Returns the token balance of a given address.

        Args:
            address: The address to check the balance of.

        Returns:
            The token balance of the address specified.
        """
        return Wad(self._contract.call().balanceOf(address.address))

    def allowance_of(self, address: Address, payee: Address) -> Wad:
        """Returns the current allowance of a specified `payee` (delegate account).

        Allowance is an ERC20 concept allowing the `payee` (delegate account) to spend a fixed amount of tokens
        on behalf of the token owner (`address`).

        Args:
            address: The address to check the allowance for (it's the address the tokens can be spent from).
            payee: The address of the delegate account (it's the address that can spend the tokens).

        Returns:
            The allowance of the `payee` specified in regards to the `address`.
        """
        return Wad(self._contract.call().allowance(address.address, payee.address))

    def transfer(self, address: Address, value: Wad) -> Optional[Receipt]:
        """Transfers tokens to a specified address.

        Args:
            address: destination address to transfer the tokens to.
            value: the value of tokens to transfer.

        Returns:
            A `Receipt` if the Ethereum transaction (and thus the token transfer) was successful.
            `None` if the Ethereum transaction failed.
        """
        try:
            tx_hash = self._contract.transact().transfer(address.address, value.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def approve(self, payee: Address, limit: Wad) -> Optional[Receipt]:
        """Modifies the current allowance of a specified `payee` (delegate account).

        Allowance is an ERC20 concept allowing the `payee` (delegate account) to spend a fixed amount of tokens
        (`limit`) on behalf of the token owner.

        Args:
            payee: The address of the delegate account (it's the address that can spend the tokens).
            limit: The value of the allowance i.e. the value of tokens that the `payee` (delegate account)
                can spend on behalf of their owner.

        Returns:
            A `Receipt` if the Ethereum transaction (and thus the approval) was successful.
            `None` if the Ethereum transaction failed.
        """
        try:
            tx_hash = self._contract.transact().approve(payee.address, limit.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"ERC20Token(address='{self.address}')"

    @staticmethod
    def register_token(address, name):
        ERC20Token.registry[address] = name

    @staticmethod
    def token_address_by_name(token_name):
        for address, name in ERC20Token.registry.items():
            if name == token_name:
                return address
        raise Exception(f"Token {token_name} not found")
