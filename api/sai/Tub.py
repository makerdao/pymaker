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
    abi = Contract._load_abi(__name__, 'Tub.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    def air(self) -> Wad:
        """Get the amount of backing collateral"""
        return Wad(self._contract.call().air())

    def axe(self) -> Ray:
        """Get the liquidation penalty"""
        return Ray(self._contract.call().axe())

    def chi(self) -> Ray:
        """Get the internal debt price"""
        return Ray(self._contract.call().chi())

    def tax(self) -> Ray:
        """Get the stability fee"""
        return Ray(self._contract.call().tax())

    def rho(self) -> Ray:
        """Get the time of last drip"""
        return Ray(self._contract.call().tax())

    def fix(self) -> Wad:
        """Get the SAI settlement price"""
        return Wad(self._contract.call().fix())

    def joy(self) -> Wad:
        """Get the amount of surplus sai"""
        return Wad(self._contract.call().joy())

    def sai(self) -> Address:
        """Get the sai token

        Returns:
            The address of the sai token.
        """
        return Address(self._contract.call().sai())

    def sin(self) -> Address:
        """Get the sin token

        Returns:
            The address of the sin token.
        """
        return Address(self._contract.call().sin())

    def skr(self) -> Address:
        """Get the skr token

        Returns:
            The address of the skr token.
        """
        return Address(self._contract.call().skr())

    def woe(self) -> Wad:
        """Get the amount of bad debt"""
        return Wad(self._contract.call().woe())

    def fog(self) -> Wad:
        """Get the amount of skr pending liquidation"""
        return Wad(self._contract.call().fog())

    def per(self) -> Ray:
        """Get the current entry price (gem per skr)"""
        return Ray(self._contract.call().per())

    def tag(self) -> Wad:
        """Get the reference price (ref per gem)"""
        return Wad(self._contract.call().tag())

    def mat(self) -> Ray:
        """Get the liquidation ratio"""
        return Ray(self._contract.call().mat())

    def tip(self) -> Address:
        """Get the gem price feed

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
        """Get the cup details
        
        Args:
            cup_id: Id of the cup to get the details of.
            
        Returns:
            Class encapsulating cup details.
        """
        assert isinstance(cup_id, int)
        array = self._contract.call().cups(self._to_bytes32(cup_id))
        return Cup(Address(array[0]), Wad(array[1]), Wad(array[2]))

    def tab(self, cup_id: int) -> Wad:
        """Get how much debt in a cup"""
        assert isinstance(cup_id, int)
        return Wad(self._contract.call().tab(self._to_bytes32(cup_id)))

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
        """Post additional SKR collateral to a cup

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
        """Initiate liquidation of an undercollateralized cup

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
        """Buy some amount of sai to process joy (surplus)

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
        """Sell some amount of sai to process woe (bad debt)

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

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"Tub(address='{self.address}')"
