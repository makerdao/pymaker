# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
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

from pymaker import Address, Contract, Transact
from pymaker.numeric import Wad, Ray
from pymaker.token import ERC20Token
from pymaker.util import int_to_bytes32


class Cup:
    """Represents details of a single cup managed by a `Tub`.

    Notes:
        `art` is denominated in internal debt units and should not be used directly, unless you really
        know what you're doing and you know what `chi()` and `rho()` are.

    Attributes:
        cup_id: The identifier of the cup.
        lad: Address of the owner of the cup.
        art: The amount of outstanding debt (denominated in internal debt units).
        ink: The amount of SKR collateral locked in the cup.
    """
    def __init__(self, cup_id: int, lad: Address, ink: Wad, art: Wad):
        assert(isinstance(cup_id, int))
        assert(isinstance(lad, Address))
        assert(isinstance(art, Wad))
        assert(isinstance(ink, Wad))
        self.cup_id = cup_id
        self.lad = lad
        self.art = art
        self.ink = ink

    def __repr__(self):
        return f"Cup(cup_id={self.cup_id}, lad={repr(self.lad)}, art={self.art}, ink={self.ink})"


class Tub(Contract):
    """A client for the `Tub` contract.

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

    abi = Contract._load_abi(__name__, 'abi/SaiTub.abi')
    bin = Contract._load_bin(__name__, 'abi/SaiTub.bin')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3, sai: Address, sin: Address, skr: Address, gem: Address, gov: Address, pip: Address, pep: Address, vox: Address, pit: Address):
        assert(isinstance(sai, Address))
        assert(isinstance(sin, Address))
        assert(isinstance(skr, Address))
        assert(isinstance(gem, Address))
        assert(isinstance(gov, Address))
        assert(isinstance(pip, Address))
        assert(isinstance(pep, Address))
        assert(isinstance(vox, Address))
        assert(isinstance(pit, Address))

        return Tub(web3=web3, address=Contract._deploy(web3, Tub.abi, Tub.bin,
                                                       [sai.address, sin.address, skr.address, gem.address, gov.address,
                                                        pip.address, pep.address, vox.address, pit.address]))

    def set_authority(self, address: Address) -> Transact:
        assert(isinstance(address, Address))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'setAuthority', [address.address])

    def approve(self, approval_function):
        """Approve the `Tub` to access our GEM, SKR, SAI and GOV balances.

        For available approval functions (i.e. approval modes) see `directly` and `via_tx_manager`
        in `pymaker.approval`.

        Args:
            approval_function: Approval function (i.e. approval mode).
        """
        assert(callable(approval_function))

        approval_function(ERC20Token(web3=self.web3, address=self.gem()), self.address, 'Tub')
        approval_function(ERC20Token(web3=self.web3, address=self.skr()), self.address, 'Tub')
        approval_function(ERC20Token(web3=self.web3, address=self.sai()), self.address, 'Tub')
        approval_function(ERC20Token(web3=self.web3, address=self.gov()), self.address, 'Tub')

    def era(self) -> int:
        """Return the current `Tub` timestamp.

        Returns:
            Timestamp as a unix timestamp.
        """
        return self._contract.call().era()

    def tap(self) -> Address:
        """Get the address of the `Tap` contract.

        Returns:
            The address of the `Tap` contract.
        """
        return Address(self._contract.call().tap())

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

    def gov(self) -> Address:
        """Get the MKR token.

        Returns:
            The address of the MKR token.
        """
        return Address(self._contract.call().gov())

    def vox(self) -> Address:
        """Get the address of the `Vox` contract.

        Returns:
            The address of the `Vox` contract.
        """
        return Address(self._contract.call().vox())

    def pit(self) -> Address:
        """Get the governance vault.

        Returns:
            The address of the `DSVault` holding the governance tokens awaiting burn.
        """
        return Address(self._contract.call().pit())

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
        """Get the reference (GEM) price feed.

        Returns:
            The address of the reference (GEM) price feed, which could be a `DSValue`, a `DSCache`, `Mednianizer` etc.
        """
        return Address(self._contract.call().pip())

    def pep(self) -> Address:
        """Get the governance (MKR) price feed.

        Returns:
            The address of the governance (MKR) price feed, which could be a `DSValue`, a `DSCache`, `Mednianizer` etc.
        """
        return Address(self._contract.call().pep())

    def axe(self) -> Ray:
        """Get the liquidation penalty.

        Returns:
            The liquidation penalty. `1.0` means no penalty. `1.2` means 20% penalty.
        """
        return Ray(self._contract.call().axe())

    def cap(self) -> Wad:
        """Get the debt ceiling.

        Returns:
            The debt ceiling in SAI.
        """
        return Wad(self._contract.call().cap())

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
            The current Tub stage (0=Usual, 1=Caged).
        """
        return self._contract.call().reg()

    def fit(self) -> Ray:
        """Get the GEM per SKR settlement price.

        Returns:
            The GEM per SKR settlement (kill) price.
        """
        return Ray(self._contract.call().fit())

    def rho(self) -> int:
        """Get the time of the last drip.

        Returns:
            The time of the last drip as a unix timestamp.
        """
        return self._contract.call().rho()

    def tau(self) -> int:
        """Get the time of the last prod.

        Returns:
            The time of the last prod as a unix timestamp.
        """
        return self._contractTip.call().tau()

    def chi(self) -> Ray:
        """Get the internal debt price.

        Every invocation of this method calls `drip()` internally, so the value you receive is always up-to-date.
        But as calling it doesn't result in an Ethereum transaction, the actual `_chi` value in the smart
        contract storage does not get updated.

        Returns:
            The internal debt price in SAI.
        """
        return Ray(self._contract.call().chi())

    def mold_axe(self, new_axe: Ray) -> Transact:
        """Update the liquidation penalty.

        Args:
            new_axe: The new value of the liquidation penalty (`axe`). `1.0` means no penalty. `1.2` means 20% penalty.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_axe, Ray)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'mold', [bytes('axe', 'utf-8'), new_axe.value])

    def mold_cap(self, new_cap: Wad) -> Transact:
        """Update the debt ceiling.

        Args:
            new_cap: The new value of the debt ceiling (`cap`), in SAI.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_cap, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'mold', [bytes('cap', 'utf-8'), new_cap.value])

    def mold_mat(self, new_mat: Ray) -> Transact:
        """Update the liquidation ratio.

        Args:
            new_mat: The new value of the liquidation ratio (`mat`). `1.5` means the liquidation ratio is 150%.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_mat, Ray)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'mold', [bytes('mat', 'utf-8'), new_mat.value])

    def mold_tax(self, new_tax: Ray) -> Transact:
        """Update the stability fee.

        Args:
            new_tax: The new per-second value of the stability fee (`tax`). `1.0` means no stability fee.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_tax, Ray)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'mold', [bytes('tax', 'utf-8'), new_tax.value])

    def mold_gap(self, new_gap: Wad) -> Transact:
        """Update the current spread (`gap`) for `join` and `exit`.

        Args:
            new_tax: The new value of the spread (`gap`). `1.0` means no spread, `1.01` means 1% spread.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_gap, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'mold', [bytes('gap', 'utf-8'), new_gap.value])

    def drip(self) -> Transact:
        """Recalculate the internal debt price (`chi`).

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'drip', [])

    def prod(self) -> Transact:
        """Recalculate the accrued holder fee (`par`).

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abiTip, self.tip(), self._contractTip, 'prod', [])

    def din(self) -> Wad:
        """Get the amount of total debt.

        Returns:
            The amount of total debt in SAI.
        """
        return Wad(self._contract.call().din())

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

    def tag(self) -> Ray:
        """Get the reference price (REF per SKR).

        The price is read from the price feed (`tip()`) every time this method gets called.
        Its value is actually the value from the feed (REF per GEM) multiplied by `per()` (GEM per SKR).

        Returns:
            The reference price (REF per SKR).
        """
        return Ray(self._contract.call().tag())

    def per(self) -> Ray:
        """Get the current average entry/exit price (GEM per SKR).

        In order to get the price that will be actually used on `join()` or `exit()`, see
        `ask()` and `bid()` respectively. The difference is due to the spread (`gap`).

        Returns:
            The current GEM per SKR price.
        """
        return Ray(self._contract.call().per())

    def gap(self) -> Wad:
        """Get the current spread for `join` and `exit`.

        Returns:
            The current spread for `join` and `exit`. `1.0` means no spread, `1.01` means 1% spread.
        """
        return Wad(self._contract.call().gap())

    def bid(self, amount: Wad) -> Wad:
        """Get the current `exit()`.

        Returns:
            The amount of GEM you will get for `amount` SKR in `join()`.
        """
        assert(isinstance(amount, Wad))

        return Wad(self._contract.call().bid(amount.value))

    def ask(self, amount: Wad) -> Wad:
        """Get the current `join()` price.

        Returns:
            The amount of GEM you will have to pay to get `amount` SKR fromm `join()`.
        """
        assert(isinstance(amount, Wad))

        return Wad(self._contract.call().ask(amount.value))

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
        array = self._contract.call().cups(int_to_bytes32(cup_id))
        return Cup(cup_id, Address(array[0]), Wad(array[1]), Wad(array[2]))

    def tab(self, cup_id: int) -> Wad:
        """Get the amount of debt in a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Amount of debt in the cup, in SAI.
        """
        assert isinstance(cup_id, int)
        return Wad(self._contract.call().tab(int_to_bytes32(cup_id)))

    def ink(self, cup_id: int) -> Wad:
        """Get the amount of SKR collateral locked in a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Amount of SKR collateral locked in the cup, in SKR.
        """
        assert isinstance(cup_id, int)
        return Wad(self._contract.call().ink(int_to_bytes32(cup_id)))

    def lad(self, cup_id: int) -> Address:
        """Get the owner of a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Address of the owner of the cup.
        """
        assert isinstance(cup_id, int)
        return Address(self._contract.call().lad(int_to_bytes32(cup_id)))

    def safe(self, cup_id: int) -> bool:
        """Determine if a cup is safe.

        Args:
            cup_id: Id of the cup

        Returns:
            `True` if the cup is safe. `False` otherwise.
        """
        assert isinstance(cup_id, int)
        return self._contract.call().safe(int_to_bytes32(cup_id))

    def join(self, amount_in_skr: Wad) -> Transact:
        """Buy SKR for GEMs.

        Args:
            amount_in_skr: The amount of SKRs to buy for GEM.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(amount_in_skr, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'join', [amount_in_skr.value])

    def exit(self, amount_in_skr: Wad) -> Transact:
        """Sell SKR for GEMs.

        Args:
            amount_in_skr: The amount of SKR to sell for GEMs.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(amount_in_skr, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'exit', [amount_in_skr.value])

    #TODO make it return the id of the newly created cup
    def open(self) -> Transact:
        """Create a new cup.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'open', [])

    def shut(self, cup_id: int) -> Transact:
        """Close a cup.

        Involves calling `wipe()` and `free()` internally in order to clear all remaining SAI debt and free
        all remaining SKR collateral.

        Args:
            cup_id: Id of the cup to close.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(cup_id, int)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'shut', [int_to_bytes32(cup_id)])

    def lock(self, cup_id: int, amount_in_skr: Wad) -> Transact:
        """Post additional SKR collateral to a cup.

        Args:
            cup_id: Id of the cup to post the collateral into.
            amount_in_skr: The amount of collateral to post, in SKR.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_skr, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'lock',
                        [int_to_bytes32(cup_id), amount_in_skr.value])

    def free(self, cup_id: int, amount_in_skr: Wad) -> Transact:
        """Remove excess SKR collateral from a cup.

        Args:
            cup_id: Id of the cup to remove the collateral from.
            amount_in_skr: The amount of collateral to remove, in SKR.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_skr, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'free',
                        [int_to_bytes32(cup_id), amount_in_skr.value])

    def draw(self, cup_id: int, amount_in_sai: Wad) -> Transact:
        """Issue the specified amount of SAI stablecoins.

        Args:
            cup_id: Id of the cup to issue the SAI from.
            amount_in_sai: The amount SAI to be issued.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_sai, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'draw',
                        [int_to_bytes32(cup_id), amount_in_sai.value])

    def wipe(self, cup_id: int, amount_in_sai: Wad) -> Transact:
        """Repay some portion of existing SAI debt.

        Args:
            cup_id: Id of the cup to repay the SAI to.
            amount_in_sai: The amount SAI to be repaid.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(cup_id, int)
        assert isinstance(amount_in_sai, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'wipe',
                        [int_to_bytes32(cup_id), amount_in_sai.value])

    def give(self, cup_id: int, new_lad: Address) -> Transact:
        """Transfer ownership of a cup.

        Args:
            cup_id: Id of the cup to transfer ownership of.
            new_lad: New owner of the cup.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(cup_id, int)
        assert isinstance(new_lad, Address)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'give',
                        [int_to_bytes32(cup_id), new_lad.address])

    def bite(self, cup_id: int) -> Transact:
        """Initiate liquidation of an undercollateralized cup.

        Args:
            cup_id: Id of the cup to liquidate.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(cup_id, int)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'bite', [int_to_bytes32(cup_id)])

    def __eq__(self, other):
        assert(isinstance(other, Tub))
        return self.address == other.address

    def __repr__(self):
        return f"Tub('{self.address}')"


class Tap(Contract):
    """A client for the `Tap` contract.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Tap` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/SaiTap.abi')
    bin = Contract._load_bin(__name__, 'abi/SaiTap.bin')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3, tub: Address):
        assert(isinstance(tub, Address))
        return Tap(web3=web3, address=Contract._deploy(web3, Tap.abi, Tap.bin, [tub.address]))

    def set_authority(self, address: Address) -> Transact:
        assert(isinstance(address, Address))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'setAuthority', [address.address])

    def approve(self, approval_function):
        """Approve the `Tap` to access our SAI, SKR and GEM balances.

        For available approval functions (i.e. approval modes) see `directly` and `via_tx_manager`
        in `pymaker.approval`.

        Args:
            approval_function: Approval function (i.e. approval mode).
        """
        assert(callable(approval_function))

        tub = Tub(web3=self.web3, address=self.tub())

        approval_function(ERC20Token(web3=self.web3, address=self.sai()), self.address, 'Tap')
        approval_function(ERC20Token(web3=self.web3, address=self.skr()), self.address, 'Tap')
        approval_function(ERC20Token(web3=self.web3, address=tub.gem()), self.address, 'Tap')

    def tub(self) -> Address:
        """Get the address of the `Tub` contract.

        Returns:
            The address of the `Tub` contract.
        """
        return Address(self._contract.call().tub())

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

    def woe(self) -> Wad:
        """Get the amount of bad debt.

        Returns:
            The amount of bad debt in SAI.
        """
        return Wad(self._contract.call().woe())

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

    def gap(self) -> Wad:
        """Get the current spread for `boom` and `bust`.

        Returns:
            The current spread for `boom` and `bust`. `1.0` means no spread, `1.01` means 1% spread.
        """
        return Wad(self._contract.call().gap())

    def mold_gap(self, new_gap: Wad) -> Transact:
        """Update the current spread (`gap`) for `boom` and `bust`.

        Args:
            new_gap: The new value of the spread (`gap`). `1.0` means no spread, `1.01` means 1% spread.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_gap, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'mold', [bytes('gap', 'utf-8'), new_gap.value])

    def s2s(self) -> Ray:
        """Get the current SKR per SAI rate (for `boom` and `bust`).

        Returns:
            The current SKR per SAI rate.
        """
        return Ray(self._contract.call().s2s())

    def bid(self, amount_in_skr: Wad) -> Wad:
        """Get the current price of `amount_in_skr` SKR in SAI for `boom`.

        Returns:
            The amount in SAI which will be received from `boom` in return of
                `amount_in_skr` SKR.
        """
        return Wad(self._contract.call().bid(amount_in_skr.value))

    def ask(self, amount_in_skr: Wad) -> Wad:
        """Get the current price of `amount_in_skr` SKR in SAI for `bust`.

        Returns:
            The amount in SAI which will be consumed by `bust` if we want
                to receive `amount_in_skr` SKR from it.
        """
        return Wad(self._contract.call().ask(amount_in_skr.value))

    def boom(self, amount_in_skr: Wad) -> Transact:
        """Buy some amount of SAI to process `joy` (surplus).

        Args:
            amount_in_skr: The amount of SKR we want to send in order to receive SAI.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(amount_in_skr, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'boom', [amount_in_skr.value])

    def bust(self, amount_in_skr: Wad) -> Transact:
        """Sell some amount of SAI to process `woe` (bad debt).

        Args:
            amount_in_skr: The amount of SKR we want to receive in exchange for our SAI.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(amount_in_skr, Wad)
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'bust', [amount_in_skr.value])

    def cash(self, amount_in_sai: Wad) -> Transact:
        """Exchange SAI to GEM after cage.

        Args:
            amount_in_sai: The amount of SAI to exchange to GEM.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'cash', [amount_in_sai.value])

    def mock(self, amount_in_sai: Wad) -> Transact:
        """Exchange GEM to SAI after cage.

        Args:
            amount_in_sai: The amount of SAI to buy for GEM.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'mock', [amount_in_sai.value])

    def __eq__(self, other):
        assert(isinstance(other, Tap))
        return self.address == other.address

    def __repr__(self):
        return f"Tap('{self.address}')"


class Top(Contract):
    """A client for the `Top` contract.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Top` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/SaiTop.abi')
    bin = Contract._load_bin(__name__, 'abi/SaiTop.bin')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3, tub: Address, tap: Address):
        assert(isinstance(tub, Address))
        assert(isinstance(tap, Address))
        return Top(web3=web3, address=Contract._deploy(web3, Top.abi, Top.bin, [tub.address, tap.address]))

    def set_authority(self, address: Address) -> Transact:
        assert(isinstance(address, Address))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'setAuthority', [address.address])

    def fix(self) -> Ray:
        """Get the GEM per SAI settlement price.

        Returns:
            The GEM per SAI settlement (kill) price.
        """
        return Ray(self._contract.call().fix())

    def cage(self) -> Transact:
        """Force settlement of the system at a current price.

        Returns:
            A :py:class:`pymaker.Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'cage', [])

    # TODO vent

    def __eq__(self, other):
        assert(isinstance(other, Top))
        return self.address == other.address

    def __repr__(self):
        return f"Top('{self.address}')"


class Vox(Contract):
    """A client for the `Vox` contract.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Vox` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/SaiVox.abi')
    bin = Contract._load_bin(__name__, 'abi/SaiVox.bin')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3, per: Ray):
        assert(isinstance(per, Ray))
        return Vox(web3=web3, address=Contract._deploy(web3, Vox.abi, Vox.bin, [per.value]))

    def set_authority(self, address: Address) -> Transact:
        assert(isinstance(address, Address))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'setAuthority', [address.address])

    def era(self) -> int:
        """Return the current `Vox` timestamp.

        Returns:
            Timestamp as a unix timestamp.
        """
        return self._contract.call().era()

    def par(self) -> Ray:
        """Get the accrued holder fee (REF per SAI).

        Every invocation of this method calls `prod()` internally, so the value you receive is always up-to-date.
        But as calling it doesn't result in an Ethereum transaction, the actual `_par` value in the smart
        contract storage does not get updated.

        Returns:
            The accrued holder fee.
        """
        return Ray(self._contract.call().par())

    def __eq__(self, other):
        assert(isinstance(other, Vox))
        return self.address == other.address

    def __repr__(self):
        return f"Vox('{self.address}')"
