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
from api.sai.Cup import Cup


class Tub(Contract):
    """A client for the `Tub` contract, the primary contract driving the `SAI Stablecoin System`.

    SAI is a simple version of the diversely collateralized DAI stablecoin.

    In this model there is one type of underlying collateral (called gems).
    The SKR token represents claims on the system's excess gems, and is the
    only admissible type of collateral.  Gems can be converted to/from SKR.

    Any transfers of SAI or SKR are done using the normal ERC20 interface;
    until settlement mode is triggered, SAI users should only need ERC20.
    ``ERC20Token`` class may be used for it.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Tub` contract.
    """

    abiTub = Contract._load_abi(__name__, 'abi/Tub.abi')
    abiJar = Contract._load_abi(__name__, 'abi/SaiJar.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abiTub)(address=address.address)
        self._contractJar = web3.eth.contract(abi=self.abiJar)(address=self._contract.call().jar())

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

    def pit(self) -> Address:
        """Get the liquidator vault.

        Returns:
            The address of the `DSVault` holding the bad debt.
        """
        return Address(self._contract.call().pit())

    def pot(self) -> Address:
        """Get the good debt vault.

        Returns:
            The address of the `DSVault` holding the good debt.
        """
        return Address(self._contract.call().pot())

    def skr(self) -> Address:
        """Get the SKR token.

        Returns:
            The address of the SKR token.
        """
        return Address(self._contract.call().skr())

    def gem(self) -> Address:
        """Get the collateral token (eg. W-ETH).

        Returns:
            The address of the collateral token.
        """
        return Address(self._contract.call().gem())

    def pip(self) -> Address:
        """Get the GEM price feed.

        You can get the current feed value by calling `tag()`.

        Returns:
            The address of the GEM price feed, which could be a `DSValue`, a `DSCache`, a `Mednianizer` etc.
        """
        return Address(self._contractJar.call().pip())

    def tip(self) -> Address:
        """Get the target price engine.

        Returns:
            The address of the target price engine. It is an internal component of Sai.
        """
        return Address(self._contract.call().tip())

    def axe(self) -> Ray:
        """Get the liquidation penalty.

        Returns:
            The liquidation penalty. `1.0` means no penalty. `1.2` means 20% penalty.
        """
        return Ray(self._contract.call().axe())

    def hat(self) -> Wad:
        """Get the debt ceiling.

        Returns:
            The debt ceiling in SAI.
        """
        return Wad(self._contract.call().hat())

    def mat(self) -> Ray:
        """Get the liquidation ratio.

        Returns:
            The liquidation ratio. `1.5` means the liquidation ratio is 150%.
        """
        return Ray(self._contract.call().mat())

    def tax(self) -> Ray:
        """Get the stability fee.

        Returns:
            Per-second value of the stability fee. `1.0` means no stability fee.
        """
        return Ray(self._contract.call().tax())

    def reg(self) -> int:
        """Get the Tub stage ('register').

        Returns:
            The current Tub stage (0=Usual, 1=Caged, 2=Empty).
        """
        return self._contract.call().reg()

    def fix(self) -> Wad:
        """Get the SAI settlement price.
        
        Returns:
            The SAI settlement (kill) price (in GEM per SAI).
        """
        return Wad(self._contract.call().fix())

    def par(self) -> Ray:
        """Get the GEM per SKR price just before settlement.

        Returns:
            The GEM per SKR price saved just before settlement.
        """
        return Ray(self._contract.call().par())

    def rho(self) -> int:
        """Get the time of the last drip.

        Returns:
            The time of the last drip as a unix timestamp.
        """
        return self._contract.call().rho()

    def chi(self) -> Ray:
        """Get the internal debt price.

        Every invocation of this method calls `drip()` internally, so the value we receive is always up-to-date.
        But as calling it doesn't result in an Ethereum transaction, the actual `_chi` value in the smart
        contract storage does not get updated.

        Returns:
            The internal debt price in SAI.
        """
        return Ray(self._contract.call().chi())

    def chop(self, new_axe: Ray) -> Optional[Receipt]:
        """Update the liquidation penalty.

        Args:
            new_axe: The new value of the liquidation penalty (`axe`). `1.0` means no penalty. `1.2` means 20% penalty.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(new_axe, Ray)
        try:
            tx_hash = self._contract.transact().chop(new_axe.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def cork(self, new_hat: Wad) -> Optional[Receipt]:
        """Update the debt ceiling.

        Args:
            new_hat: The new value of the debt ceiling (`hat`), in SAI.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(new_hat, Wad)
        try:
            tx_hash = self._contract.transact().cork(new_hat.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def cuff(self, new_mat: Ray) -> Optional[Receipt]:
        """Update the liquidation ratio.

        Args:
            new_mat: The new value of the liquidation ratio (`mat`). `1.5` means the liquidation ratio is 150%.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(new_mat, Ray)
        try:
            tx_hash = self._contract.transact().cuff(new_mat.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def crop(self, new_tax: Ray) -> Optional[Receipt]:
        """Update the stability fee.

        Args:
            new_tax: The new per-second value of the stability fee (`tax`). `1.0` means no stability fee.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(new_tax, Ray)
        try:
            tx_hash = self._contract.transact().crop(new_tax.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def drip(self) -> Optional[Receipt]:
        """Recalculate the internal debt price.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        try:
            tx_hash = self._contract.transact().drip()
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def ice(self) -> Wad:
        """Get the amount of good debt.

        Returns:
            The amount of good debt in SAI.
        """
        return Wad(self._contract.call().ice())

    def woe(self) -> Wad:
        """Get the amount of bad debt.

        Returns:
            The amount of bad debt in SAI.
        """
        return Wad(self._contract.call().woe())

    def pie(self) -> Wad:
        """Get the amount of raw collateral.

        Returns:
            The amount of raw collateral in GEM.
        """
        return Wad(self._contract.call().pie())

    def air(self) -> Wad:
        """Get the amount of backing collateral.

        Returns:
            The amount of backing collateral in SKR.
        """
        return Wad(self._contract.call().air())

    def fog(self) -> Wad:
        """Get the amount of SKR pending liquidation.

        Returns:
            The amount of SKR pending liquidation, in SKR.
        """
        return Wad(self._contract.call().fog())

    #TODO beware that it doesn't call drip() underneath so if `tax`>1.0 we won't get an up-to-date value of joy()
    def joy(self) -> Wad:
        """Get the amount of surplus SAI.

        Surplus SAI can be processed using `boom()`.

        Returns:
            The amount of surplus SAI accumulated in the Tub.
        """
        return Wad(self._contract.call().joy())

    def tag(self) -> Wad:
        """Get the reference price (REF per SKR).

        The price is read from the price feed (`tip()`) every time this method gets called.
        It's value is actually the value from the feed (REF per GEM) multiplied by `per()` (GEM per SKR).

        Returns:
            The reference price (REF per SKR).
        """
        return Wad(self._contract.call().tag())

    def per(self) -> Ray:
        """Get the current entry price (GEM per SKR).

        Returns:
            The current GEM per SKR price.
        """
        return Ray(self._contract.call().per())

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
        """Get the amount of debt in a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Amount of debt in the cup, in SAI.
        """
        assert isinstance(cup_id, int)
        return Wad(self._contract.call().tab(self._to_bytes32(cup_id)))

    def ink(self, cup_id: int) -> Wad:
        """Get the amount of SKR collateral locked in a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Amount of SKR collateral locked in the cup, in SKR.
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
        """Determine if a cup is safe.

        Args:
            cup_id: Id of the cup

        Returns:
            `True` if the cup is safe. `False` otherwise.
        """
        assert isinstance(cup_id, int)
        return self._contract.call().safe(self._to_bytes32(cup_id))

    def join(self, amount_in_gem: Wad) -> Optional[Receipt]:
        """Buy SKR for GEMs.

        Args:
            amount_in_gem: The amount of GEMs to buy SKR for.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(amount_in_gem, Wad)
        try:
            tx_hash = self._contract.transact().join(amount_in_gem.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def exit(self, amount_in_skr: Wad) -> Optional[Receipt]:
        """Sell SKR for GEMs.

        Args:
            amount_in_skr: The amount of SKR to sell for GEMs.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(amount_in_skr, Wad)
        try:
            tx_hash = self._contract.transact().exit(amount_in_skr.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    #TODO make it return the id of the newly created cup
    def open(self) -> Optional[Receipt]:
        """Create a new cup.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        try:
            tx_hash = self._contract.transact().open()
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def shut(self, cup_id: int) -> Optional[Receipt]:
        """Close a cup.

        Involves calling `wipe()` and `free()` internally in order to clear all remaining SAI debt and free
        all remaining SKR collateral.

        Args:
            cup_id: Id of the cup to close.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(cup_id, int)
        try:
            tx_hash = self._contract.transact().shut(self._to_bytes32(cup_id))
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def lock(self, cup_id: int, amount_in_skr: Wad) -> Optional[Receipt]:
        """Post additional SKR collateral to a cup.

        Args:
            cup_id: Id of the cup to post the collateral into.
            amount_in_skr: The amount of collateral to post, in SKR.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_skr, Wad)
        try:
            tx_hash = self._contract.transact().lock(self._to_bytes32(cup_id), amount_in_skr.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def free(self, cup_id: int, amount_in_skr: Wad) -> Optional[Receipt]:
        """Remove excess SKR collateral from a cup.

        Args:
            cup_id: Id of the cup to remove the collateral from.
            amount_in_skr: The amount of collateral to remove, in SKR.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_skr, Wad)
        try:
            tx_hash = self._contract.transact().free(self._to_bytes32(cup_id), amount_in_skr.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def draw(self, cup_id: int, amount_in_sai: Wad) -> Optional[Receipt]:
        """Issue the specified amount of SAI stablecoins.

        Args:
            cup_id: Id of the cup to issue the SAI from.
            amount_in_sai: The amount SAI to be issued.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_sai, Wad)
        try:
            tx_hash = self._contract.transact().draw(self._to_bytes32(cup_id), amount_in_sai.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def wipe(self, cup_id: int, amount_in_sai: Wad) -> Optional[Receipt]:
        """Repay some portion of existing SAI debt.

        Args:
            cup_id: Id of the cup to repay the SAI to.
            amount_in_sai: The amount SAI to be repaid.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_sai, Wad)
        try:
            tx_hash = self._contract.transact().wipe(self._to_bytes32(cup_id), amount_in_sai.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def give(self, cup_id: int, new_lad: Address) -> Optional[Receipt]:
        """Transfer ownership of a cup.

        Args:
            cup_id: Id of the cup to transfer ownership of.
            new_lad: New owner of the cup.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(cup_id, int)
        assert isinstance(new_lad, Address)
        try:
            tx_hash = self._contract.transact().give(self._to_bytes32(cup_id), new_lad.address)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def bite(self, cup_id: int) -> Optional[Receipt]:
        """Initiate liquidation of an undercollateralized cup.

        Args:
            cup_id: Id of the cup to liquidate.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(cup_id, int)
        try:
            tx_hash = self._contract.transact().bite(self._to_bytes32(cup_id))
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def boom(self, amount_in_skr: Wad) -> Optional[Receipt]:
        """Buy some amount of SAI to process `joy` (surplus).

        Args:
            amount_in_skr: The amount of SKR we want to send in order to receive SAI.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(amount_in_skr, Wad)
        try:
            tx_hash = self._contract.transact().boom(amount_in_skr.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None

    def bust(self, amount_in_skr: Wad) -> Optional[Receipt]:
        """Sell some amount of SAI to process `woe` (bad debt).

        Args:
            amount_in_skr: The amount of SKR we want to receive in exchange for our SAI.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(amount_in_skr, Wad)
        try:
            tx_hash = self._contract.transact().bust(amount_in_skr.value)
            return self._prepare_receipt(self.web3, tx_hash)
        except:
            return None
        
    # TODO cage
    # TODO cash
    # TODO vent

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"Tub(address='{self.address}')"
