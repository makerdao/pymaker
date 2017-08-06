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

from web3 import Web3

from api import Contract, Address, Receipt, Calldata
from api.numeric import Wad


class ERC20Token(Contract):
    """A client for a standard ERC20 token contract.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the ERC20 token.
    """

    abi = Contract._load_abi(__name__, 'abi/ERC20Token.abi')
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
        return self._transact(self.web3, f"ERC20Token('{self.address}').transfer('{address}', '{value}')",
                              lambda: self._contract.transact().transfer(address.address, value.value))

    def transfer_calldata(self, address: Address, value: Wad) -> Optional[Receipt]:
        return Calldata(self.web3.eth.contract(abi=self.abi).encodeABI('transfer', [address.address, value.value]))

    def approve(self, payee: Address, limit: Wad = Wad(2**256 - 1)) -> Optional[Receipt]:
        """Modifies the current allowance of a specified `payee` (delegate account).

        Allowance is an ERC20 concept allowing the `payee` (delegate account) to spend a fixed amount of tokens
        (`limit`) on behalf of the token owner.

        If `limit` is omitted, a maximum possible value is granted.

        Args:
            payee: The address of the delegate account (it's the address that can spend the tokens).
            limit: The value of the allowance i.e. the value of tokens that the `payee` (delegate account)
                can spend on behalf of their owner.

        Returns:
            A `Receipt` if the Ethereum transaction (and thus the approval) was successful.
            `None` if the Ethereum transaction failed.
        """
        return self._transact(self.web3, f"ERC20Token('{self.address}').approve('{payee}', '{limit}')",
                              lambda: self._contract.transact().approve(payee.address, limit.value))

    def approve_calldata(self, payee: Address, limit: Wad = Wad(2**256 - 1)) -> Calldata:
        return Calldata(self.web3.eth.contract(abi=self.abi).encodeABI('approve', [payee.address, limit.value]))

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"ERC20Token('{self.address}')"

    @staticmethod
    def register_token(address: Address, name):
        ERC20Token.registry[address] = name

    @staticmethod
    def token_address_by_name(token_name):
        for address, name in ERC20Token.registry.items():
            if name == token_name:
                return address
        raise Exception(f"Token {token_name} not found")

    @staticmethod
    def token_name_by_address(token_address: Address):
        return ERC20Token.registry[token_address]


class DSToken(ERC20Token):
    abi = Contract._load_abi(__name__, 'abi/DSToken.abi')
    bin = Contract._load_bin(__name__, 'abi/DSToken.bin')

    @staticmethod
    def deploy(web3: Web3, symbol: str):
        assert(isinstance(symbol, str))
        return DSToken(web3=web3, address=Contract._deploy(web3, DSToken.abi, DSToken.bin, [symbol]))

    def set_authority(self, address: Address) -> Optional[Receipt]:
        assert(isinstance(address, Address))
        return self._transact(self.web3, f"DSToken('{self.address}').setAuthority('{address}')",
                              lambda: self._contract.transact().setAuthority(address.address))

    def mint(self, amount: Wad) -> Optional[Receipt]:
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"DSToken('{self.address}').mint('{amount}')",
                              lambda: self._contract.transact().mint(amount.value))

    def burn(self, amount: Wad) -> Optional[Receipt]:
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"DSToken('{self.address}').burn('{amount}')",
                              lambda: self._contract.transact().burn(amount.value))

    def __repr__(self):
        return f"DSToken('{self.address}')"


class DSEthToken(ERC20Token):
    """A client for a the `DSEthToken` contract.

    `DSEthToken`, also known as _ETH Wrapper_ or _W-ETH_, is a smart contract into which you can deposit
    raw ETH and then deal with it like with any other ERC20 token. In addition to the `deposit()`
    and `withdraw()` methods, it implements the standard ERC20 token API.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSEthToken` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSEthToken.abi')
    bin = Contract._load_bin(__name__, 'abi/DSEthToken.bin')

    @staticmethod
    def deploy(web3: Web3, args=[]):
        return DSEthToken(web3=web3, address=Contract._deploy(web3, DSEthToken.abi, DSEthToken.bin, args))

    def __init__(self, web3, address):
        super().__init__(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def deposit(self, amount: Wad) -> Optional[Receipt]:
        """Deposits `amount` of raw ETH to `DSEthToken`.

        Args:
            amount: Amount of raw ETH to be deposited to `DSEthToken`.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the amount has been deposited.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"DSEthToken('{self.address}').deposit() with value='{amount}'",
                              lambda: self._contract.transact({'value': amount.value}).deposit())

    def withdraw(self, amount: Wad) -> Optional[Receipt]:
        """Withdraws `amount` of raw ETH from `DSEthToken`.

        The withdrawn ETH will get transferred to the calling account.

        Args:
            amount: Amount of raw ETH to be withdrawn from `DSEthToken`.

        Returns:
            A `Receipt` if the Ethereum transaction was successful and the amount has been withdrawn.
            `None` if the Ethereum transaction failed.
        """
        assert(isinstance(amount, Wad))
        return self._transact(self.web3, f"DSEthToken('{self.address}').withdraw('{amount}')",
                              lambda: self._contract.transact().withdraw(amount.value))

    def __repr__(self):
        return f"DSEthToken('{self.address}')"
