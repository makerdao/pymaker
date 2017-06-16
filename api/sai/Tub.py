# This file is part of "maker.py".
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
from api.sai.Cup import Cup


class Tub(Contract):
    """A client for a `Tub` contract, a Maker contract driving the `Sai Stablecoin System`.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Tub`.
    """

    abi = Contract._load_abi(__name__, 'Tub.abi')

    def __init__(self, web3: Web3, address: Address):
        """Creates a new client for a `Tub` contract.

        Notes:
            Existence of a contract on the Ethereum blockchain under given address is verified the moment
                the instance of this class is created.

        Args:
            web3: An instance of `Web` from `web3.py`.
            address: Ethereum address of the `Tub`.
        """
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def air(self) -> Wad:
        """Get the amount of backing collateral."""
        return Wad(self._contract.call().air())

    def axe(self) -> Ray:
        """Get the liquidation penalty."""
        return Ray(self._contract.call().axe())

    def chi(self) -> Ray:
        """Get the internal debt price."""
        return Ray(self._contract.call().chi())

    def tax(self) -> Ray:
        """Get the stability fee."""
        return Ray(self._contract.call().tax())

    def hat(self) -> Wad:
        """Get the debt ceiling."""
        return Wad(self._contract.call().hat())

    def rho(self) -> int:
        """Get the time of the last drip."""
        return self._contract.call().rho()

    def fix(self) -> Wad:
        """Get the SAI settlement price"""
        return Wad(self._contract.call().fix())

    def joy(self) -> Wad:
        """Get the amount of surplus SAI"""
        return Wad(self._contract.call().joy())

    def gem(self) -> Address:
        """Get the collateral token.

        Returns:
            The address of the collateral token.
        """
        return Address(self._contract.call().gem())

    def sai(self) -> Address:
        """Get the SAI token.

        Returns:
            The address of the SAI token.
        """
        return Address(self._contract.call().sai())

    def sin(self) -> Address:
        """Get the SIN token.

        Returns:
            The address of the SIN token.
        """
        return Address(self._contract.call().sin())

    def skr(self) -> Address:
        """Get the SKR token.

        Returns:
            The address of the SKR token.
        """
        return Address(self._contract.call().skr())

    def ice(self) -> Wad:
        """Get the amount of good debt."""
        return Wad(self._contract.call().ice())

    def woe(self) -> Wad:
        """Get the amount of bad debt."""
        return Wad(self._contract.call().woe())

    def fog(self) -> Wad:
        """Get the amount of skr pending liquidation."""
        return Wad(self._contract.call().fog())

    def pie(self) -> Wad:
        """Get the amount of raw collateral."""
        return Wad(self._contract.call().pie())

    def par(self) -> Ray:
        """Get the gem per skr price just before settlement."""
        return Ray(self._contract.call().par())

    def per(self) -> Ray:
        """Get the current entry price (gem per skr)."""
        return Ray(self._contract.call().per())

    def tag(self) -> Wad:
        """Get the reference price (ref per gem)."""
        return Wad(self._contract.call().tag())

    def mat(self) -> Ray:
        """Get the liquidation ratio."""
        return Ray(self._contract.call().mat())

    def pot(self) -> Address:
        """Get the good debt vault.

        Returns:
            The address of the DSVault holding the good debt.
        """
        return Address(self._contract.call().pot())

    def tip(self) -> Address:
        """Get the gem price feed.

        Returns:
            The address of the gem price feed, which could be a DSValue, DSCache, Mednianizer etc.
        """
        return Address(self._contract.call().tip())

    def cupi(self) -> int:
        """Get the last cup id

        Returns:
            The id of the last cup created. Zero if no cups have been created so far.
        """
        return self._contract.call().cupi()

    def cups(self, cup_id: int) -> Cup:
        """Get the cup details.
        
        Args:
            cup_id: Id of the cup to get the details of.
            
        Returns:
            Class encapsulating cup details.
        """
        assert isinstance(cup_id, int)
        array = self._contract.call().cups(self._to_bytes32(cup_id))
        return Cup(Address(array[0]), Wad(array[1]), Wad(array[2]))

    def tab(self, cup_id: int) -> Wad:
        """Get how much debt in a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Amount of debt in the cup.
        """
        assert isinstance(cup_id, int)
        return Wad(self._contract.call().tab(self._to_bytes32(cup_id)))

    def ink(self, cup_id: int) -> Wad:
        """Get the amount of skr collateral locked in a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Amount of skr collateral locked in the cup.
        """
        assert isinstance(cup_id, int)
        return Wad(self._contract.call().ink(self._to_bytes32(cup_id)))

    def lad(self, cup_id: int) -> Address:
        """Get the owner of a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Address of the owner of the cup.
        """
        assert isinstance(cup_id, int)
        return Address(self._contract.call().lad(self._to_bytes32(cup_id)))

    def safe(self, cup_id: int) -> bool:
        """Determine if a cup is safe

        Args:
            cup_id: Id of the cup

        Returns:
            True if the cup is safe. False otherwise.
        """
        assert isinstance(cup_id, int)
        return self._contract.call().safe(self._to_bytes32(cup_id))

    def lock(self, cup_id: int, amount_in_skr: Wad) -> Optional[Receipt]:
        """Post additional SKR collateral to a cup.

        Args:
            cup_id: Id of the cup to post the collateral into.
            amount_in_skr: The amount of collateral to post.

        Returns:
            A Receipt if the Ethereum transaction was successful.
            None if the Ethereum transaction failed.
        """
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_skr, Wad)
        try:
            tx_hash = self._contract.transact().lock(self._to_bytes32(cup_id), amount_in_skr.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def bite(self, cup_id: int) -> Optional[Receipt]:
        """Initiate liquidation of an undercollateralized cup.

        Args:
            cup_id: Id of the cup to bite.

        Returns:
            A Receipt if the Ethereum transaction was successful.
            None if the Ethereum transaction failed.
        """
        assert isinstance(cup_id, int)
        try:
            tx_hash = self._contract.transact().bite(self._to_bytes32(cup_id))
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def boom(self, amount_in_skr: Wad) -> Optional[Receipt]:
        """Buy some amount of sai to process joy (surplus).

        Args:
            amount_in_skr: The amount of SKR we want to send in order to receive SAI.

        Returns:
            A Receipt if the Ethereum transaction was successful.
            None if the Ethereum transaction failed.
        """
        assert isinstance(amount_in_skr, Wad)
        try:
            tx_hash = self._contract.transact().boom(amount_in_skr.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def bust(self, amount_in_skr: Wad) -> Optional[Receipt]:
        """Sell some amount of sai to process woe (bad debt).

        Args:
            amount_in_skr: The amount of SKR we want to receive in exchange for our SAI.

        Returns:
            A Receipt if the Ethereum transaction was successful.
            None if the Ethereum transaction failed.
        """
        assert isinstance(amount_in_skr, Wad)
        try:
            tx_hash = self._contract.transact().bust(amount_in_skr.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def reg(self) -> int:
        """Get the Tub stage ('register').

        Returns:
            The current Tub stage (0=Usual, 1=Caged, 2=Empty).
        """
        return self._contract.call().reg()

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"Tub(address='{self.address}')"
