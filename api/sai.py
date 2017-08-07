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

from api import Address, Wad, Contract, Receipt, Calldata, Transact
from api.numeric import Ray
from api.token import ERC20Token
from api.util import int_to_bytes32


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
    def __init__(self, cup_id: int, lad: Address, art: Wad, ink: Wad):
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
    binTub = Contract._load_bin(__name__, 'abi/Tub.bin')
    abiTip = Contract._load_abi(__name__, 'abi/Tip.abi')
    abiJar = Contract._load_abi(__name__, 'abi/SaiJar.abi')
    abiJug = Contract._load_abi(__name__, 'abi/SaiJug.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contractTub = web3.eth.contract(abi=self.abiTub)(address=address.address)
        self._contractTip = web3.eth.contract(abi=self.abiTip)(address=self._contractTub.call().tip())
        self._contractJar = web3.eth.contract(abi=self.abiJar)(address=self._contractTub.call().jar())
        self._contractJug = web3.eth.contract(abi=self.abiJug)(address=self._contractTub.call().jug())

    @staticmethod
    def deploy(web3: Web3, jar: Address, jug: Address, pot: Address, pit: Address, tip: Address):
        assert(isinstance(jar, Address))
        assert(isinstance(jug, Address))
        assert(isinstance(pot, Address))
        assert(isinstance(pit, Address))
        assert(isinstance(tip, Address))
        return Tub(web3=web3, address=Contract._deploy(web3, Tub.abiTub, Tub.binTub,
                                                       [jar.address, jug.address, pot.address, pit.address, tip.address]))

    def set_authority(self, address: Address):
        assert(isinstance(address, Address))
        Transact(self, self.web3, self.abiTub, self.address, self._contractTub, 'setAuthority', [address.address]).transact()
        Transact(self, self.web3, self.abiTip, self.tip(), self._contractTip, 'setAuthority', [address.address]).transact()
        Transact(self, self.web3, self.abiJar, self.jar(), self._contractJar, 'setAuthority', [address.address]).transact()
        Transact(self, self.web3, self.abiJug, self.jug(), self._contractJug, 'setAuthority', [address.address]).transact()

    def approve(self, approval_function):
        approval_function(ERC20Token(web3=self.web3, address=self.gem()), self.jar(), 'Tub.jar')
        approval_function(ERC20Token(web3=self.web3, address=self.skr()), self.jar(), 'Tub.jar')
        approval_function(ERC20Token(web3=self.web3, address=self.sai()), self.pot(), 'Tub.pot')
        approval_function(ERC20Token(web3=self.web3, address=self.skr()), self.pit(), 'Tub.pit')
        approval_function(ERC20Token(web3=self.web3, address=self.sai()), self.pit(), 'Tub.pit')

    def sai(self) -> Address:
        """Get the SAI token.

        Returns:
            The address of the SAI token.
        """
        return Address(self._contractTub.call().sai())

    def sin(self) -> Address:
        """Get the SIN token.

        Returns:
            The address of the SIN token.
        """
        return Address(self._contractTub.call().sin())

    def jug(self) -> Address:
        """Get the SAI/SIN tracker.

        Returns:
            The address of the SAI/SIN tracker token.
        """
        return Address(self._contractTub.call().jug())

    def jar(self) -> Address:
        """Get the collateral vault.

        Returns:
            The address of the `SaiJar` vault. It is an internal component of Sai.
        """
        return Address(self._contractTub.call().jar())

    def pit(self) -> Address:
        """Get the liquidator vault.

        Returns:
            The address of the `DSVault` holding the bad debt.
        """
        return Address(self._contractTub.call().pit())

    def pot(self) -> Address:
        """Get the good debt vault.

        Returns:
            The address of the `DSVault` holding the good debt.
        """
        return Address(self._contractTub.call().pot())

    def skr(self) -> Address:
        """Get the SKR token.

        Returns:
            The address of the SKR token.
        """
        return Address(self._contractTub.call().skr())

    def gem(self) -> Address:
        """Get the collateral token (eg. W-ETH).

        Returns:
            The address of the collateral token.
        """
        return Address(self._contractTub.call().gem())

    def pip(self) -> Address:
        """Get the GEM price feed.

        Returns:
            The address of the GEM price feed, which could be a `DSValue`, a `DSCache`, a `Mednianizer` etc.
        """
        return Address(self._contractJar.call().pip())

    def tip(self) -> Address:
        """Get the target price engine.

        Returns:
            The address of the target price engine. It is an internal component of Sai.
        """
        return Address(self._contractTub.call().tip())

    def axe(self) -> Ray:
        """Get the liquidation penalty.

        Returns:
            The liquidation penalty. `1.0` means no penalty. `1.2` means 20% penalty.
        """
        return Ray(self._contractTub.call().axe())

    def hat(self) -> Wad:
        """Get the debt ceiling.

        Returns:
            The debt ceiling in SAI.
        """
        return Wad(self._contractTub.call().hat())

    def mat(self) -> Ray:
        """Get the liquidation ratio.

        Returns:
            The liquidation ratio. `1.5` means the liquidation ratio is 150%.
        """
        return Ray(self._contractTub.call().mat())

    def tax(self) -> Ray:
        """Get the stability fee.

        Returns:
            Per-second value of the stability fee. `1.0` means no stability fee.
        """
        return Ray(self._contractTub.call().tax())

    def way(self) -> Ray:
        """Get the holder fee (interest rate).

        Returns:
            Per-second value of the holder fee. `1.0` means no holder fee.
        """
        return Ray(self._contractTip.call().way())

    def reg(self) -> int:
        """Get the Tub stage ('register').

        Returns:
            The current Tub stage (0=Usual, 1=Caged).
        """
        return self._contractTub.call().reg()

    def fit(self) -> Ray:
        """Get the GEM per SKR settlement price.

        Returns:
            The GEM per SKR settlement (kill) price.
        """
        return Ray(self._contractTub.call().fit())

    def rho(self) -> int:
        """Get the time of the last drip.

        Returns:
            The time of the last drip as a unix timestamp.
        """
        return self._contractTub.call().rho()

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
        return Ray(self._contractTub.call().chi())

    def chop(self, new_axe: Ray) -> Transact:
        """Update the liquidation penalty.

        Args:
            new_axe: The new value of the liquidation penalty (`axe`). `1.0` means no penalty. `1.2` means 20% penalty.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_axe, Ray)
        return Transact(self, self.web3, self.abiTub, self.address, self._contractTub, 'chop', [new_axe.value])

    def cork(self, new_hat: Wad) -> Transact:
        """Update the debt ceiling.

        Args:
            new_hat: The new value of the debt ceiling (`hat`), in SAI.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_hat, Wad)
        return Transact(self, self.web3, self.abiTub, self.address, self._contractTub, 'cork', [new_hat.value])

    def cuff(self, new_mat: Ray) -> Transact:
        """Update the liquidation ratio.

        Args:
            new_mat: The new value of the liquidation ratio (`mat`). `1.5` means the liquidation ratio is 150%.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_mat, Ray)
        return Transact(self, self.web3, self.abiTub, self.address, self._contractTub, 'cuff', [new_mat.value])

    def crop(self, new_tax: Ray) -> Transact:
        """Update the stability fee.

        Args:
            new_tax: The new per-second value of the stability fee (`tax`). `1.0` means no stability fee.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_tax, Ray)
        return Transact(self, self.web3, self.abiTub, self.address, self._contractTub, 'crop', [new_tax.value])

    def coax(self, new_way: Ray) -> Transact:
        """Update the holder fee.

        Args:
            new_way: The new per-second value of the holder fee (`way`). `1.0` means no holder fee.

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        assert isinstance(new_way, Ray)
        return Transact(self, self.web3, self.abiTub, self.address, self._contractTub, 'coax', [new_way.value])

    def drip(self) -> Transact:
        """Recalculate the internal debt price (`chi`).

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abiTub, self.address, self._contractTub, 'drip', [])

    def prod(self) -> Transact:
        """Recalculate the accrued holder fee (`par`).

        Returns:
            A `Transact` instance, which can be used to trigger the transaction.
        """
        return Transact(self, self.web3, self.abiTip, self.tip(), self._contractTip, 'prod', [])

    def ice(self) -> Wad:
        """Get the amount of good debt.

        Returns:
            The amount of good debt in SAI.
        """
        return Wad(self._contractTub.call().ice())

    def pie(self) -> Wad:
        """Get the amount of raw collateral.

        Returns:
            The amount of raw collateral in GEM.
        """
        return Wad(self._contractTub.call().pie())

    def air(self) -> Wad:
        """Get the amount of backing collateral.

        Returns:
            The amount of backing collateral in SKR.
        """
        return Wad(self._contractTub.call().air())

    def tag(self) -> Wad:
        """Get the reference price (REF per SKR).

        The price is read from the price feed (`tip()`) every time this method gets called.
        Its value is actually the value from the feed (REF per GEM) multiplied by `per()` (GEM per SKR).

        Returns:
            The reference price (REF per SKR).
        """
        return Wad(self._contractJar.call().tag())

    def par(self) -> Wad:
        """Get the accrued holder fee (REF per SAI).

        Every invocation of this method calls `prod()` internally, so the value you receive is always up-to-date.
        But as calling it doesn't result in an Ethereum transaction, the actual `_par` value in the smart
        contract storage does not get updated.

        Returns:
            The accrued holder fee.
        """
        return Wad(self._contractTip.call().par())

    def per(self) -> Ray:
        """Get the current average entry/exit price (GEM per SKR).

        In order to get the price that will be actually used on `join()` or `exit()`, see
        `jar_ask()` and `jar_bid()` respectively.

        Returns:
            The current GEM per SKR price.
        """
        return Ray(self._contractJar.call().per())

    # TODO these prefixed methods are ugly, the ultimate solution would be to have a class per smart contract
    def jar_gap(self) -> Wad:
        """Get the current spread for `join` and `exit`.

        Returns:
            The current spread for `join` and `exit`. `1.0` means no spread, `1.01` means 1% spread.
        """
        return Wad(self._contractJar.call().gap())

    # TODO these prefixed methods are ugly, the ultimate solution would be to have a class per smart contract
    def jar_jump(self, new_gap: Wad) -> Optional[Receipt]:
        """Update the current spread (`gap`) for `join` and `exit`.

        Args:
            new_tax: The new value of the spread (`gap`). `1.0` means no spread, `1.01` means 1% spread.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(new_gap, Wad)
        return self._transact(self.web3, f"Jar('{self._contractTub.call().jar()}').jump('{new_gap}')",
                              lambda: self._contractJar.transact().jump(new_gap.value))

    # TODO these prefixed methods are ugly, the ultimate solution would be to have a class per smart contract
    def jar_bid(self) -> Ray:
        """Get the current `exit()` price (GEM per SKR).

        Returns:
            The GEM per SKR price that will be used on `exit()`.
        """
        return Ray(self._contractJar.call().bid())

    # TODO these prefixed methods are ugly, the ultimate solution would be to have a class per smart contract
    def jar_ask(self) -> Ray:
        """Get the current `join()` price (GEM per SKR).

        Returns:
            The GEM per SKR price that will be used on `join()`.
        """
        return Ray(self._contractJar.call().ask())

    def cupi(self) -> int:
        """Get the last cup id

        Returns:
            The id of the last cup created. Zero if no cups have been created so far.
        """
        return self._contractTub.call().cupi()

    def cups(self, cup_id: int) -> Cup:
        """Get the cup details.

        Args:
            cup_id: Id of the cup to get the details of.

        Returns:
            Class encapsulating cup details.
        """
        assert isinstance(cup_id, int)
        array = self._contractTub.call().cups(int_to_bytes32(cup_id))
        return Cup(cup_id, Address(array[0]), Wad(array[1]), Wad(array[2]))

    def tab(self, cup_id: int) -> Wad:
        """Get the amount of debt in a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Amount of debt in the cup, in SAI.
        """
        assert isinstance(cup_id, int)
        return Wad(self._contractTub.call().tab(int_to_bytes32(cup_id)))

    def ink(self, cup_id: int) -> Wad:
        """Get the amount of SKR collateral locked in a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Amount of SKR collateral locked in the cup, in SKR.
        """
        assert isinstance(cup_id, int)
        return Wad(self._contractTub.call().ink(int_to_bytes32(cup_id)))

    def lad(self, cup_id: int) -> Address:
        """Get the owner of a cup.

        Args:
            cup_id: Id of the cup.

        Returns:
            Address of the owner of the cup.
        """
        assert isinstance(cup_id, int)
        return Address(self._contractTub.call().lad(int_to_bytes32(cup_id)))

    def safe(self, cup_id: int) -> bool:
        """Determine if a cup is safe.

        Args:
            cup_id: Id of the cup

        Returns:
            `True` if the cup is safe. `False` otherwise.
        """
        assert isinstance(cup_id, int)
        return self._contractTub.call().safe(int_to_bytes32(cup_id))

    def join(self, amount_in_gem: Wad) -> Optional[Receipt]:
        """Buy SKR for GEMs.

        Args:
            amount_in_gem: The amount of GEMs to buy SKR for.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(amount_in_gem, Wad)
        return self._transact(self.web3, f"Tub('{self.address}').join('{amount_in_gem}')",
                              lambda: self._contractTub.transact().join(amount_in_gem.value))

    def join_calldata(self, amount_in_gem: Wad) -> Calldata:
        return Calldata(self.web3.eth.contract(abi=self.abiTub).encodeABI('join', [amount_in_gem]))

    def exit(self, amount_in_skr: Wad) -> Optional[Receipt]:
        """Sell SKR for GEMs.

        Args:
            amount_in_skr: The amount of SKR to sell for GEMs.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(amount_in_skr, Wad)
        return self._transact(self.web3, f"Tub('{self.address}').exit('{amount_in_skr}')",
                              lambda: self._contractTub.transact().exit(amount_in_skr.value))

    def exit_calldata(self, amount_in_skr: Wad) -> Calldata:
        return Calldata(self.web3.eth.contract(abi=self.abiTub).encodeABI('exit', [amount_in_skr]))

    #TODO make it return the id of the newly created cup
    def open(self) -> Optional[Receipt]:
        """Create a new cup.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        return self._transact(self.web3, f"Tub('{self.address}').open()",
                              lambda: self._contractTub.transact().open())

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
        return self._transact(self.web3, f"Tub('{self.address}').shut('{cup_id}')",
                              lambda: self._contractTub.transact().shut(int_to_bytes32(cup_id)))

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
        return self._transact(self.web3, f"Tub('{self.address}').lock('{cup_id}', '{amount_in_skr}')",
                              lambda: self._contractTub.transact().lock(int_to_bytes32(cup_id), amount_in_skr.value))

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
        return self._transact(self.web3, f"Tub('{self.address}').free('{cup_id}', '{amount_in_skr}')",
                              lambda: self._contractTub.transact().free(int_to_bytes32(cup_id), amount_in_skr.value))

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
        return self._transact(self.web3, f"Tub('{self.address}').draw('{cup_id}', '{amount_in_sai}')",
                              lambda: self._contractTub.transact().draw(int_to_bytes32(cup_id), amount_in_sai.value))

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
        return self._transact(self.web3, f"Tub('{self.address}').wipe('{cup_id}', '{amount_in_sai}')",
                              lambda: self._contractTub.transact().wipe(int_to_bytes32(cup_id), amount_in_sai.value))

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
        return self._transact(self.web3, f"Tub('{self.address}').give('{cup_id}', '{new_lad}')",
                              lambda: self._contractTub.transact().give(int_to_bytes32(cup_id), new_lad.address))

    def bite(self, cup_id: int) -> Optional[Receipt]:
        """Initiate liquidation of an undercollateralized cup.

        Args:
            cup_id: Id of the cup to liquidate.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(cup_id, int)
        return self._transact(self.web3, f"Tub('{self.address}').bite('{cup_id}')",
                              lambda: self._contractTub.transact().bite(int_to_bytes32(cup_id)))

    def __eq__(self, other):
        assert(isinstance(other, Tub))
        return self.address == other.addressTub

    def __repr__(self):
        return f"Tub('{self.address}')"


class Tap(Contract):
    """A client for the `Tap` contract, on of the contracts driving the `SAI Stablecoin System`.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Tap` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/Tap.abi')
    bin = Contract._load_bin(__name__, 'abi/Tap.bin')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

    @staticmethod
    def deploy(web3: Web3, tub: Address, pit: Address):
        assert(isinstance(tub, Address))
        assert(isinstance(pit, Address))
        return Tap(web3=web3, address=Contract._deploy(web3, Tap.abi, Tap.bin, [tub.address, pit.address]))

    def set_authority(self, address: Address) -> Transact:
        assert(isinstance(address, Address))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'setAuthority', [address.address])

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

    def jump(self, new_gap: Wad) -> Optional[Receipt]:
        """Update the current spread (`gap`) for `boom` and `bust`.

        Args:
            new_tax: The new value of the spread (`gap`). `1.0` means no spread, `1.01` means 1% spread.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(new_gap, Wad)
        return self._transact(self.web3, f"Tap('{self.address}').jump('{new_gap}')",
                              lambda: self._contract.transact().jump(new_gap.value))

    def s2s(self) -> Wad:
        """Get the current SKR per SAI rate (for `boom` and `bust`).

        Returns:
            The current SKR per SAI rate.
        """
        return Wad(self._contract.call().s2s())

    def bid(self) -> Wad:
        """Get the current price of SKR in SAI for `boom`.

        Returns:
            The SKR in SAI price that will be used on `boom()`.
        """
        return Wad(self._contract.call().bid())

    def ask(self) -> Wad:
        """Get the current price of SKR in SAI for `bust`.

        Returns:
            The SKR in SAI price that will be used on `bust()`.
        """
        return Wad(self._contract.call().ask())

    def boom(self, amount_in_skr: Wad) -> Optional[Receipt]:
        """Buy some amount of SAI to process `joy` (surplus).

        Args:
            amount_in_skr: The amount of SKR we want to send in order to receive SAI.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(amount_in_skr, Wad)
        return self._transact(self.web3, f"Tap('{self.address}').boom('{amount_in_skr}')",
                              lambda: self._contract.transact().boom(amount_in_skr.value))

    def boom_calldata(self, amount_in_skr: Wad) -> Calldata:
        return Calldata(self.web3.eth.contract(abi=self.abi).encodeABI('boom', [amount_in_skr]))

    def bust(self, amount_in_skr: Wad) -> Optional[Receipt]:
        """Sell some amount of SAI to process `woe` (bad debt).

        Args:
            amount_in_skr: The amount of SKR we want to receive in exchange for our SAI.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(amount_in_skr, Wad)
        return self._transact(self.web3, f"Tap('{self.address}').bust('{amount_in_skr}')",
                              lambda: self._contract.transact().bust(amount_in_skr.value))

    def bust_calldata(self, amount_in_skr: Wad) -> Calldata:
        return Calldata(self.web3.eth.contract(abi=self.abi).encodeABI('bust', [amount_in_skr]))

    def __eq__(self, other):
        assert(isinstance(other, Tap))
        return self.address == other.address

    def __repr__(self):
        return f"Tap('{self.address}')"


class Top(Contract):
    """A client for the `Top` contract, one of the `SAI Stablecoin System` contracts.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Top` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/Top.abi')
    bin = Contract._load_bin(__name__, 'abi/Top.bin')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)

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

    # TODO cage
    # TODO cash
    # TODO vent

    def __eq__(self, other):
        assert(isinstance(other, Top))
        return self.address == other.address

    def __repr__(self):
        return f"Top('{self.address}')"


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

    abi = Contract._load_abi(__name__, 'abi/SaiLPC.abi')
    abiTip = Contract._load_abi(__name__, 'abi/Tip.abi')

    def __init__(self, web3: Web3, address: Address):
        self.web3 = web3
        self.address = address
        self._assert_contract_exists(web3, address)
        self._contract = web3.eth.contract(abi=self.abi)(address=address.address)
        self._contractTip = web3.eth.contract(abi=self.abiTip)(address=self._contract.call().tip())

    def approve(self, approval_function):
        approval_function(ERC20Token(web3=self.web3, address=self.ref()), self.address, 'Lpc')
        approval_function(ERC20Token(web3=self.web3, address=self.alt()), self.address, 'Lpc')

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
            The current value of the spread. `1.0` means no spread. `1.02` means 2% spread.
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
            new_gap: The new value of the spread (`gap`). `1.0` means no spread. `1.02` means 2% spread.

        Returns:
            A `Receipt` if the Ethereum transaction was successful.
            `None` if the Ethereum transaction failed.
        """
        assert isinstance(new_gap, Wad)
        return self._transact(self.web3, f"Lpc('{self.address}').jump('{new_gap}')",
                              lambda: self._contract.transact().jump(new_gap.value))

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

    def par(self) -> Wad:
        """Get the accrued holder fee.

        Every invocation of this method calls `prod()` internally, so the value you receive is always up-to-date.
        But as calling it doesn't result in an Ethereum transaction, the actual `_par` value in the smart
        contract storage does not get updated.

        Returns:
            The accrued holder fee.
        """
        return Wad(self._contractTip.call().par())

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
        return self._transact(self.web3, f"Lpc('{self.address}').pool('{token}', '{amount}')",
                              lambda: self._contract.transact().pool(token.address, amount.value))

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
        return self._transact(self.web3, f"Lpc('{self.address}').exit('{token}', '{amount}')",
                              lambda: self._contract.transact().exit(token.address, amount.value))

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
        return self._transact(self.web3, f"Lpc('{self.address}').take('{token}', '{amount}')",
                              lambda: self._contract.transact().take(token.address, amount.value))

    def take_calldata(self, token: Address, amount: Wad) -> Calldata:
        return Calldata(self.web3.eth.contract(abi=self.abi).encodeABI('take', [token.address, amount.value]))

    def __eq__(self, other):
        return self.address == other.address

    def __repr__(self):
        return f"Lpc('{self.address}')"
