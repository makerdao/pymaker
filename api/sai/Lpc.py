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

from api.Address import Address
from api.Contract import Contract
from api.Ray import Ray
from api.Receipt import Receipt
from api.Wad import Wad


class Lpc(Contract):
    """A client for the `SaiLPC` contract, a simple two-token liquidity pool created together for Sai.

    `SaiLPC` relies on an external price feed (the `tip`).

    Makers
    - `pool()` their gems and receive LPS tokens, which are a claim on the pool.
    - `exit()` and trade their LPS tokens for a share of the gems in the pool.

    Takers
    - `take()` and exchange one gem for another, whilst paying a fee (the `gap`). The collected fee goes into the pool.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `SaiLPC` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/Lpc.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def ref(self) -> Address:
        """Get the ref token.

        Returns:
            The address of the ref token.
        """
        return Address(self._contract.call().ref())

    def alt(self) -> Address:
        """Get the alt token.

        Returns:
            The address of the alt token.
        """
        return Address(self._contract.call().alt())

    def pip(self) -> Address:
        """Get the price feed (giving refs per alt).

        You can get the current feed value by calling `tag()`.

        Returns:
            The address of the price feed, which could be a `DSValue`, a `DSCache`, a `Mednianizer` etc.
        """
        return Address(self._contract.call().pip())

    def tip(self) -> Address:
        """Get the target price engine.

        Returns:
            The address of the target price engine. It is an internal component of Sai.
        """
        return Address(self._contract.call().tip())

    def gap(self) -> Wad:
        """Get the spread, charged on `take()`.

        Returns:
            The current value of the spread.
        """
        return Wad(self._contract.call().gap())

    def lps(self) -> Address:
        """Get the LPS token (liquidity provider shares).

        Returns:
            The address of the LPS token.
        """
        return Address(self._contract.call().lps())

    def jump(self, new_gap: Wad) -> Optional[Receipt]:
        """Update the spread.

        Args:
            new_gap: The new value of the spread (`gap`).

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(new_gap, Wad)
        try:
            tx_hash = self._contract.transact().jump(new_gap.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def tag(self) -> Wad:
        """Get the current price (refs per alt).

        The price is read from the price feed (`tip()`) every time this method gets called.

        Returns:
            The current price (refs per alt).
        """
        return Wad(self._contract.call().tag())

    def pie(self) -> Wad:
        """Get the total pool value (in ref).

        Returns:
            The the total pool value (in ref).
        """
        return Wad(self._contract.call().pie())

    def per(self) -> Ray:
        """Get the lps per ref ratio.

        Returns:
            The current lps per ref ratio.
        """
        return Ray(self._contract.call().per())

    def pool(self, token: Address, amount: Wad) -> Optional[Receipt]:
        """Enter the pool, get LPS for ref or alt.

        The `amount` of token `token` will be transferred from your account to the pool.
        In return you will receive some number of LPS tokens, calculated accordingly to `per()`.

        LPS tokens are needed to claim the tokens back (either refs or alts) with `exit()`.

        Args:
            token: The token to enter the pool with (either ref or alt).
            amount: The value (in `token`) to enter the pool with.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(token, Address)
        assert isinstance(amount, Wad)
        try:
            tx_hash = self._contract.transact().pool(token.address, amount.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def exit(self, token: Address, amount: Wad) -> Optional[Receipt]:
        """Exit the pool, exchange LPS for ref or alt.

        The `amount` of token `token` will be credited to your account, as long as there are tokens in the
        pool available. The corresponding number of LPS tokens, calculated accordingly to `per()`, will be
        taken from your account.

        Args:
            token: The token you want to receive from the pool (either ref or alt).
            amount: The value (in `token`) you want to receive from the pool.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(token, Address)
        assert isinstance(amount, Wad)
        try:
            tx_hash = self._contract.transact().exit(token.address, amount.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def take(self, token: Address, amount: Wad) -> Optional[Receipt]:
        """Perform an exchange.

        If `token` is ref, credits `amount` of ref to your account, taking the equivalent amount of alts from you.
        If `token` is alt, credits `amount` of alt to your account, taking the equivalent amount of refs from you.

        The current price (`tag`) is used as the exchange rate.

        Args:
            token: The token you want to get from the pool (either ref or alt).
            amount: The value (in `token`) you want to get from the pool.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(token, Address)
        assert isinstance(amount, Wad)
        try:
            tx_hash = self._contract.transact().take(token.address, amount.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None
    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"Tub(address='{self.address}')"
