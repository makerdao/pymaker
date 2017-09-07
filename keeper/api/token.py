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

from keeper.api import Contract, Address, Receipt, Transact
from keeper.api.numeric import Wad


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
        assert(isinstance(address, Address))

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
        assert(isinstance(address, Address))
        assert(isinstance(payee, Address))

        return Wad(self._contract.call().allowance(address.address, payee.address))

    def transfer(self, address: Address, value: Wad) -> Transact:
        """Transfers tokens to a specified address.

        Args:
            address: Destination address to transfer the tokens to.
            value: The value of tokens to transfer.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(address, Address))
        assert(isinstance(value, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'transfer', [address.address, value.value])

    def approve(self, payee: Address, limit: Wad = Wad(2**256 - 1)) -> Transact:
        """Modifies the current allowance of a specified `payee` (delegate account).

        Allowance is an ERC20 concept allowing the `payee` (delegate account) to spend a fixed amount of tokens
        (`limit`) on behalf of the token owner.

        If `limit` is omitted, a maximum possible value is granted.

        Args:
            payee: The address of the delegate account (it's the address that can spend the tokens).
            limit: The value of the allowance i.e. the value of tokens that the `payee` (delegate account)
                can spend on behalf of their owner.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(payee, Address))
        assert(isinstance(limit, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'approve', [payee.address, limit.value])

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
    """A client for the `DSToken` contract.

    You can find the source code of the `DSToken` contract here:
    <https://github.com/dapphub/ds-token>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSToken` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSToken.abi')
    bin = Contract._load_bin(__name__, 'abi/DSToken.bin')

    @staticmethod
    def deploy(web3: Web3, symbol: str):
        """Deploy a new instance of the `DSToken` contract.

        Args:
            web3: An instance of `Web` from `web3.py`.
            symbol: Symbol of the new token.

        Returns:
            A `DSToken` class instance.
        """
        assert(isinstance(symbol, str))
        return DSToken(web3=web3, address=Contract._deploy(web3, DSToken.abi, DSToken.bin, [symbol]))

    def authority(self) -> Address:
        """Return the current `authority` of a `DSAuth`-ed contract.

        Returns:
            The address of the current `authority`.
        """
        return Address(self._contract.call().authority())

    def set_authority(self, address: Address) -> Transact:
        """Set the `authority` of a `DSAuth`-ed contract.

        Args:
            address: The address of the new `authority`.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(address, Address))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'setAuthority', [address.address])

    def mint(self, amount: Wad) -> Transact:
        """Increase the total supply of the token.

        Args:
            amount: The amount to increase the total supply by.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(amount, Wad))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'mint', [amount.value])

    def burn(self, amount: Wad) -> Transact:
        """Decrease the total supply of the token.

        Args:
            amount: The amount to decrease the total supply by.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(amount, Wad))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'burn', [amount.value])

    def __repr__(self):
        return f"DSToken('{self.address}')"


class DSEthToken(ERC20Token):
    """A client for the `DSEthToken` contract.

    `DSEthToken`, also known as ETH Wrapper or W-ETH, is a contract into which you can deposit
    raw ETH and then deal with it like with any other ERC20 token. In addition to the `deposit()`
    and `withdraw()` methods, it implements the standard ERC20 token API.

    You can find the source code of the `DSEthToken` contract here:
    <https://github.com/dapphub/ds-eth-token>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `DSEthToken` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/DSEthToken.abi')
    bin = Contract._load_bin(__name__, 'abi/DSEthToken.bin')

    @staticmethod
    def deploy(web3: Web3):
        """Deploy a new instance of the `DSEthToken` contract.

        Args:
            web3: An instance of `Web` from `web3.py`.

        Returns:
            A `DSEthToken` class instance.
        """
        return DSEthToken(web3=web3, address=Contract._deploy(web3, DSEthToken.abi, DSEthToken.bin, []))

    def __init__(self, web3, address):
        super().__init__(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def deposit(self, amount: Wad) -> Transact:
        """Deposits `amount` of raw ETH to `DSEthToken`.

        Args:
            amount: Amount of raw ETH to be deposited to `DSEthToken`.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(amount, Wad))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'deposit', [], {'value': amount.value})

    def withdraw(self, amount: Wad) -> Transact:
        """Withdraws `amount` of raw ETH from `DSEthToken`.

        The withdrawn ETH will get transferred to the calling account.

        Args:
            amount: Amount of raw ETH to be withdrawn from `DSEthToken`.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert(isinstance(amount, Wad))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'withdraw', [amount.value])

    def __repr__(self):
        return f"DSEthToken('{self.address}')"
