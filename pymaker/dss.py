# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2018-2021 bargst, EdNoepel
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

import logging
from datetime import datetime
from pprint import pformat
from typing import List

from web3 import Web3

from pymaker import Address, Contract, Transact
from pymaker.ilk import Ilk
from pymaker.logging import LogNote
from pymaker.token import DSToken, ERC20Token
from pymaker.numeric import Wad, Ray, Rad


logger = logging.getLogger()


class Urn:
    """Models one CDP for a single collateral type and account.  Note the "address of the Urn" is merely the address
    of the CDP holder.
    """

    def __init__(self, address: Address, ilk: Ilk = None, ink: Wad = None, art: Wad = None):
        assert isinstance(address, Address)
        assert isinstance(ilk, Ilk) or (ilk is None)
        assert isinstance(ink, Wad) or (ink is None)
        assert isinstance(art, Wad) or (art is None)

        self.address = address
        self.ilk = ilk
        self.ink = ink
        self.art = art

    def toBytes(self):
        addr_str = self.address.address
        return Web3.toBytes(hexstr='0x' + addr_str[2:].zfill(64))

    @staticmethod
    def fromBytes(urn: bytes):
        assert isinstance(urn, bytes)

        address = Address(Web3.toHex(urn[-20:]))
        return Urn(address)

    def __eq__(self, other):
        assert isinstance(other, Urn)

        return (self.address == other.address) and (self.ilk == other.ilk)

    def __repr__(self):
        repr = ''
        if self.ilk:
            repr += f'[{self.ilk.name}]'
        if self.ink:
            repr += f' ink={self.ink}'
        if self.art:
            repr += f' art={self.art}'
        if repr:
            repr = f'[{repr.strip()}]'
        return f"Urn('{self.address}'){repr}"


class Vat(Contract):
    """A client for the `Vat` contract, which manages accounting for all Urns (CDPs).

    Ref. <https://github.com/makerdao/dss/blob/master/src/vat.sol>
    """

    # Identifies vault holders and collateral types they have frobbed
    class LogFrob:
        def __init__(self, lognote: LogNote):
            assert isinstance(lognote, LogNote)

            self.ilk = str(Web3.toText(lognote.arg1)).replace('\x00', '')
            self.urn = Address(Web3.toHex(lognote.arg2)[26:])
            self.collateral_owner = Address(Web3.toHex(lognote.arg3)[26:])
            self.dai_recipient = Address(Web3.toHex(lognote.get_bytes_at_index(3))[26:])
            self.dink = Wad(int.from_bytes(lognote.get_bytes_at_index(4), byteorder="big", signed=True))
            self.dart = Wad(int.from_bytes(lognote.get_bytes_at_index(5), byteorder="big", signed=True))
            self.block = lognote.block
            self.tx_hash = lognote.tx_hash

        def __repr__(self):
            return f"LogFrob({pformat(vars(self))})"

    # Tracks movement of stablecoin between urns
    class LogMove:
        def __init__(self, lognote: LogNote):
            assert isinstance(lognote, LogNote)

            self.src = Address(Web3.toHex(lognote.arg1)[26:])
            self.dst = Address(Web3.toHex(lognote.arg2)[26:])
            self.dart = Rad(int.from_bytes(lognote.get_bytes_at_index(2), byteorder="big", signed=True))
            self.block = lognote.block
            self.tx_hash = lognote.tx_hash

        def __repr__(self):
            return f"LogMove({pformat(vars(self))})"

    # Shows vaults being split or merged
    class LogFork:
        def __init__(self, lognote: LogNote):
            assert isinstance(lognote, LogNote)

            self.ilk = str(Web3.toText(lognote.arg1)).replace('\x00', '')
            self.src = Address(Web3.toHex(lognote.arg2)[26:])
            self.dst = Address(Web3.toHex(lognote.arg3)[26:])
            self.dink = Wad(int.from_bytes(lognote.get_bytes_at_index(3), byteorder="big", signed=True))
            self.dart = Wad(int.from_bytes(lognote.get_bytes_at_index(4), byteorder="big", signed=True))
            self.block = lognote.block
            self.tx_hash = lognote.tx_hash

        def __repr__(self):
            return f"LogFork({pformat(vars(self))})"

    abi = Contract._load_abi(__name__, 'abi/Vat.abi')
    bin = Contract._load_bin(__name__, 'abi/Vat.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def init(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'init', [ilk.toBytes()])

    def live(self) -> bool:
        return self._contract.functions.live().call() > 0

    def wards(self, address: Address):
        assert isinstance(address, Address)

        return bool(self._contract.functions.wards(address.address).call())

    def hope(self, address: Address):
        assert isinstance(address, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'hope', [address.address])

    def can(self, sender: Address, usr: Address):
        assert isinstance(sender, Address)
        assert isinstance(usr, Address)

        return bool(self._contract.functions.can(sender.address, usr.address).call())

    def ilk(self, name: str) -> Ilk:
        assert isinstance(name, str)

        b32_ilk = Ilk(name).toBytes()
        (art, rate, spot, line, dust) = self._contract.functions.ilks(b32_ilk).call()

        # We could get "ink" from the urn, but caller must provide an address.
        return Ilk(name, rate=Ray(rate), ink=Wad(0), art=Wad(art), spot=Ray(spot), line=Rad(line), dust=Rad(dust))

    def gem(self, ilk: Ilk, urn: Address) -> Wad:
        assert isinstance(ilk, Ilk)
        assert isinstance(urn, Address)

        return Wad(self._contract.functions.gem(ilk.toBytes(), urn.address).call())

    def dai(self, urn: Address) -> Rad:
        assert isinstance(urn, Address)

        return Rad(self._contract.functions.dai(urn.address).call())

    def sin(self, urn: Address) -> Rad:
        assert isinstance(urn, Address)

        return Rad(self._contract.functions.sin(urn.address).call())

    def urn(self, ilk: Ilk, address: Address) -> Urn:
        assert isinstance(ilk, Ilk)
        assert isinstance(address, Address)

        (ink, art) = self._contract.functions.urns(ilk.toBytes(), address.address).call()
        return Urn(address, ilk, Wad(ink), Wad(art))

    def debt(self) -> Rad:
        return Rad(self._contract.functions.debt().call())

    def vice(self) -> Rad:
        return Rad(self._contract.functions.vice().call())

    def line(self) -> Rad:
        """ Total debt ceiling """
        return Rad(self._contract.functions.Line().call())

    def flux(self, ilk: Ilk, src: Address, dst: Address, wad: Wad) -> Transact:
        """Move Ilk balance in Vat from source address to destiny address

        Args:
            ilk: Identifies the type of collateral.
            src: Source of the collateral (address of the source).
            dst: Destiny of the collateral (address of the recipient).
            wad: Amount of collateral to move.
        """
        assert isinstance(ilk, Ilk)
        assert isinstance(src, Address)
        assert isinstance(dst, Address)
        assert isinstance(wad, Wad)

        flux_args = [ilk.toBytes(), src.address, dst.address, wad.value]
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'flux', flux_args)

    def move(self, src: Address, dst: Address, rad: Rad) -> Transact:
        """Move Dai balance in Vat from source address to destiny address

        Args:
            src: Source of the dai (address of the source).
            dst: Destiny of the dai (address of the recipient).
            rad: Amount of dai to move.
        """
        assert isinstance(src, Address)
        assert isinstance(dst, Address)
        assert isinstance(rad, Rad)

        move_args = [src.address, dst.address, rad.value]
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'move', move_args)

    def fork(self, ilk: Ilk, src: Address, dst: Address, dink: Wad, dart: Wad) -> Transact:
        """Split a Vault - binary approval or splitting/merging Vault's

        Args:
            ilk: Identifies the type of collateral.
            src: Address of the source Urn.
            dst: Address of the destiny Urn.
            dink: Amount of collateral to exchange.
            dart: Amount of stable coin debt to exchange.
        """
        assert isinstance(ilk, Ilk)
        assert isinstance(src, Address)
        assert isinstance(dst, Address)
        assert isinstance(dink, Wad)
        assert isinstance(dart, Wad)

        fork_args = [ilk.toBytes(), src.address, dst.address, dink.value, dart.value]
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'fork', fork_args)

    def frob(self, ilk: Ilk, urn_address: Address, dink: Wad, dart: Wad, collateral_owner=None, dai_recipient=None):
        """Adjust amount of collateral and reserved amount of Dai for the CDP

        Args:
            ilk: Identifies the type of collateral.
            urn_address: CDP holder (address of the Urn).
            dink: Amount of collateral to add/remove.
            dart: Adjust CDP debt (amount of Dai available for borrowing).
            collateral_owner: Holder of the collateral used to fund the CDP.
            dai_recipient: Party receiving the Dai.
        """
        assert isinstance(ilk, Ilk)
        assert isinstance(urn_address, Address)
        assert isinstance(dink, Wad)
        assert isinstance(dart, Wad)
        assert isinstance(collateral_owner, Address) or (collateral_owner is None)
        assert isinstance(dai_recipient, Address) or (dai_recipient is None)

        # Usually these addresses are the same as the account holding the urn
        v = collateral_owner or urn_address
        w = dai_recipient or urn_address
        assert isinstance(v, Address)
        assert isinstance(w, Address)

        self.validate_frob(ilk, urn_address, dink, dart)

        if v == urn_address and w == urn_address:
            logger.info(f"frobbing {ilk.name} urn {urn_address.address} with dink={dink}, dart={dart}")
        else:
            logger.info(f"frobbing {ilk.name} urn {urn_address.address} "
                        f"with dink={dink} from {v.address}, "
                        f"dart={dart} for {w.address}")

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'frob', [ilk.toBytes(), urn_address.address, v.address, w.address, dink.value, dart.value])

    def get_wipe_all_dart(self, ilk: Ilk, urn: Address) -> Wad:
        """Returns the amount of Dai required to wipe an urn without leaving any dust
        adapted from https://github.com/makerdao/dss-proxy-actions/blob/master/src/DssProxyActions.sol#L200"""
        assert isinstance(urn, Address)
        assert isinstance(ilk, Ilk)
        assert ilk.rate >= Ray.from_number(1)

        # dai: Rad = self.dai(urn)
        rad: Rad = Rad(self.urn(ilk, urn).art) * Rad(ilk.rate)  # - dai
        wad: Wad = Wad(rad)
        wad = wad + Wad(1) if Rad(wad) < rad else wad
        return wad

    def validate_frob(self, ilk: Ilk, address: Address, dink: Wad, dart: Wad):
        """Helps diagnose `frob` transaction failures by asserting on `require` conditions in the contract"""

        def r(value, decimals=1):  # rounding function
            return round(float(value), decimals)

        def f(value, decimals=1):  # formatting function
            return f"{r(value):16,.{decimals}f}"

        assert isinstance(ilk, Ilk)
        assert isinstance(address, Address)
        assert isinstance(dink, Wad)
        assert isinstance(dart, Wad)

        assert self.live()  # system is live

        urn = self.urn(ilk, address)
        ilk = self.ilk(ilk.name)
        assert ilk.rate != Ray(0)  # ilk has been initialised

        ink = urn.ink + dink
        art = urn.art + dart
        ilk_art = ilk.art + dart

        logger.debug(f"System     | debt {f(self.debt())} | ceiling {f(self.line())}")
        logger.debug(f"Collateral | debt {f(Ray(ilk_art) * ilk.rate)} | ceiling {f(ilk.line)}")

        dtab = Rad(ilk.rate * Ray(dart))
        tab = ilk.rate * art
        debt = self.debt() + dtab
        logger.debug(f"Frobbing ink={r(urn.ink)}, art={urn.art}, dtab={r(dtab)}, tab={tab}, "
                     f"ilk.rate={r(ilk.rate,8)}, ilk.spot={r(ilk.spot, 4)}, vat.debt={r(debt)}")

        # either debt has decreased, or debt ceilings are not exceeded
        under_collateral_debt_ceiling = Rad(Ray(ilk_art) * ilk.rate) <= ilk.line
        under_system_debt_ceiling = debt < self.line()
        calm = dart <= Wad(0) or (under_collateral_debt_ceiling and under_system_debt_ceiling)

        # urn is either less risky than before, or it is safe
        safe = (dart <= Wad(0) and dink >= Wad(0)) or tab <= Ray(ink) * ilk.spot

        # urn has no debt, or a non-dusty amount
        neat = art == Wad(0) or Rad(tab) >= ilk.dust

        if not under_collateral_debt_ceiling:
            logger.warning("collateral debt ceiling would be exceeded")
        if not under_system_debt_ceiling:
            logger.warning("system debt ceiling would be exceeded")
        if not safe:
            logger.warning("urn would be unsafe")
        if not neat:
            logger.warning("debt would not exceed dust cutoff")
        assert calm and safe and neat

    def past_frobs(self, from_block: int, to_block: int = None, ilk: Ilk = None, chunk_size=20000) -> List[LogFrob]:
        """Synchronously retrieve a list showing which ilks and urns have been frobbed.
         Args:
            from_block: Oldest Ethereum block to retrieve the events from.
            to_block: Optional newest Ethereum block to retrieve the events from, defaults to current block
            ilk: Optionally filter frobs by ilk.name
            chunk_size: Number of blocks to fetch from chain at one time, for performance tuning
         Returns:
            List of past `LogFrob` events represented as :py:class:`pymaker.dss.Vat.LogFrob` class.
        """
        return self.past_logs(from_block, to_block, ilk,
                              include_forks=False, include_moves=False, chunk_size=chunk_size)

    def past_logs(self, from_block: int, to_block: int = None, ilk: Ilk = None,
                   include_forks=True, include_moves=True, chunk_size=20000) -> List[object]:
        """Synchronously retrieve a unordered list of vat activity, optionally filtered by collateral type.
        Args:
            from_block: Oldest Ethereum block to retrieve the events from.
            to_block: Optional newest Ethereum block to retrieve the events from, defaults to current block
            ilk: Optionally filter frobs by ilk.name
            chunk_size: Number of blocks to fetch from chain at one time, for performance tuning
        Returns:
            Unordered list of past `LogFork`, `LogFrob`, and `LogMove` events.
        """
        current_block = self._contract.web3.eth.blockNumber
        assert isinstance(from_block, int)
        assert from_block <= current_block
        if to_block is None:
            to_block = current_block
        else:
            assert isinstance(to_block, int)
            assert to_block >= from_block
            assert to_block <= current_block
        assert isinstance(ilk, Ilk) or ilk is None
        assert chunk_size > 0

        logger.debug(f"Consumer requested frob data from block {from_block} to {to_block}")
        start = from_block
        end = None
        chunks_queried = 0
        retval = []
        while end is None or start <= to_block:
            chunks_queried += 1
            end = min(to_block, start+chunk_size)

            filter_params = {
                'address': self.address.address,
                'fromBlock': start,
                'toBlock': end
            }
            logger.debug(f"Querying logs from block {start} to {end} ({end-start} blocks); "
                         f"accumulated {len(retval)} logs in {chunks_queried-1} requests")

            logs = self.web3.eth.getLogs(filter_params)

            lognotes = list(map(lambda l: LogNote.from_event(l, Vat.abi), logs))

            # '0x7cdd3fde' is Vat.slip (from GemJoin.join) and '0x76088703' is Vat.frob
            logfrobs = list(filter(lambda l: l.sig == '0x76088703', lognotes))
            logfrobs = list(map(lambda l: Vat.LogFrob(l), logfrobs))
            if ilk is not None:
                logfrobs = list(filter(lambda l: l.ilk == ilk.name, logfrobs))
            retval.extend(logfrobs)

            # '0xbb35783b' is Vat.move
            if include_moves:
                logmoves = list(filter(lambda l: l.sig == '0xbb35783b', lognotes))
                logmoves = list(map(lambda l: Vat.LogMove(l), logmoves))
                retval.extend(logmoves)

            # '0x870c616d' is Vat.fork
            if include_forks:
                logforks = list(filter(lambda l: l.sig == '0x870c616d', lognotes))
                logforks = list(map(lambda l: Vat.LogFork(l), logforks))
                if ilk is not None:
                    logforks = list(filter(lambda l: l.ilk == ilk.name, logforks))
                retval.extend(logforks)

            start += chunk_size

        logger.debug(f"Found {len(retval)} logs in {chunks_queried} requests")
        return retval

    def heal(self, vice: Rad) -> Transact:
        assert isinstance(vice, Rad)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'heal', [vice.value])

    def __eq__(self, other):
        assert isinstance(other, Vat)
        return self.address == other.address

    def __repr__(self):
        return f"Vat('{self.address}')"


class Spotter(Contract):
    """A client for the `Spotter` contract, which interacts with Vat for the purpose of managing collateral prices.
    Users generally have no need to interact with this contract; it is included for unit testing purposes.

    Ref. <https://github.com/makerdao/dss-deploy/blob/master/src/poke.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/Spotter.abi')
    bin = Contract._load_bin(__name__, 'abi/Spotter.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def poke(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'poke', [ilk.toBytes()])

    def vat(self) -> Address:
        return Address(self._contract.functions.vat().call())

    def par(self) -> Ray:
        return Ray(self._contract.functions.par().call())

    def mat(self, ilk: Ilk) -> Ray:
        assert isinstance(ilk, Ilk)
        (pip, mat) = self._contract.functions.ilks(ilk.toBytes()).call()

        return Ray(mat)

    def __repr__(self):
        return f"Spotter('{self.address}')"


class Vow(Contract):
    """A client for the `Vow` contract, which manages liquidation of surplus Dai and settlement of collateral debt.
    Specifically, this contract is useful for Flap and Flop auctions.

    Ref. <https://github.com/makerdao/dss/blob/master/src/heal.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/Vow.abi')
    bin = Contract._load_bin(__name__, 'abi/Vow.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)
        self.vat = Vat(web3, Address(self._contract.functions.vat().call()))

    def rely(self, guy: Address) -> Transact:
        assert isinstance(guy, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'rely', [guy.address])

    def live(self) -> bool:
        return self._contract.functions.live().call() > 0

    def flapper(self) -> Address:
        return Address(self._contract.functions.flapper().call())

    def flopper(self) -> Address:
        return Address(self._contract.functions.flopper().call())

    def sin(self) -> Rad:
        return Rad(self._contract.functions.Sin().call())

    def sin_of(self, era: int) -> Rad:
        return Rad(self._contract.functions.sin(era).call())

    def ash(self) -> Rad:
        return Rad(self._contract.functions.Ash().call())

    def woe(self) -> Rad:
        return (self.vat.sin(self.address) - self.sin()) - self.ash()

    def wait(self) -> int:
        return int(self._contract.functions.wait().call())

    def dump(self) -> Wad:
        return Wad(self._contract.functions.dump().call())

    def sump(self) -> Rad:
        return Rad(self._contract.functions.sump().call())

    def bump(self) -> Rad:
        return Rad(self._contract.functions.bump().call())

    def hump(self) -> Rad:
        return Rad(self._contract.functions.hump().call())

    def flog(self, era: int) -> Transact:
        assert isinstance(era, int)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'flog', [era])

    def heal(self, rad: Rad) -> Transact:
        assert isinstance(rad, Rad)
        logger.info(f"Healing joy={self.vat.dai(self.address)} woe={self.woe()}")

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'heal', [rad.value])

    def kiss(self, rad: Rad) -> Transact:
        assert isinstance(rad, Rad)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kiss', [rad.value])

    def flop(self) -> Transact:
        """Initiate a debt auction"""
        logger.info(f"Initiating a flop auction with woe={self.woe()}")

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'flop', [])

    def flap(self) -> Transact:
        """Initiate a surplus auction"""
        logger.info(f"Initiating a flap auction with joy={self.vat.dai(self.address)}")

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'flap', [])

    def __repr__(self):
        return f"Vow('{self.address}')"


class Jug(Contract):
    """A client for the `Jug` contract, which manages stability fees.

    Ref. <https://github.com/makerdao/dss/blob/master/src/jug.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/Jug.abi')
    bin = Contract._load_bin(__name__, 'abi/Jug.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)
        self.vat = Vat(web3, Address(self._contract.functions.vat().call()))
        self.vow = Vow(web3, Address(self._contract.functions.vow().call()))

    def init(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'init', [ilk.toBytes()])

    def wards(self, address: Address):
        assert isinstance(address, Address)

        return bool(self._contract.functions.wards(address.address).call())

    def drip(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'drip', [ilk.toBytes()])

    def base(self) -> Ray:
        return Ray(self._contract.functions.base().call())

    def duty(self, ilk: Ilk) -> Ray:
        assert isinstance(ilk, Ilk)

        return Ray(self._contract.functions.ilks(ilk.toBytes()).call()[0])

    def rho(self, ilk: Ilk) -> int:
        assert isinstance(ilk, Ilk)

        return Web3.toInt(self._contract.functions.ilks(ilk.toBytes()).call()[1])

    def __repr__(self):
        return f"Jug('{self.address}')"


class Cat(Contract):
    """A client for the `Cat` contract, used to liquidate unsafe Urns (CDPs).
    Specifically, this contract is useful for Flip auctions.

    Ref. <https://github.com/makerdao/dss/blob/master/src/cat.sol>
    """

    # This information is read from the `Bite` event emitted from `Cat.bite`
    class LogBite:
        def __init__(self, log):
            self.ilk = Ilk.fromBytes(log['args']['ilk'])
            self.urn = Urn(Address(log['args']['urn']))
            self.ink = Wad(log['args']['ink'])
            self.art = Wad(log['args']['art'])
            self.tab = Rad(log['args']['tab'])
            self.flip = Address(log['args']['flip'])
            self.id = int(log['args']['id'])
            self.raw = log

        def era(self, web3: Web3):
            return web3.eth.getBlock(self.raw['blockNumber'])['timestamp']

        def __eq__(self, other):
            assert isinstance(other, Cat.LogBite)
            return self.__dict__ == other.__dict__

        def __repr__(self):
            return pformat(vars(self))

    abi = Contract._load_abi(__name__, 'abi/Cat.abi')
    bin = Contract._load_bin(__name__, 'abi/Cat.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)
        self.vat = Vat(web3, Address(self._contract.functions.vat().call()))
        self.vow = Vow(web3, Address(self._contract.functions.vow().call()))

    def live(self) -> bool:
        return self._contract.functions.live().call() > 0

    def can_bite(self, ilk: Ilk, urn: Urn) -> bool:
        """ Determine whether a vault can be liquidated

        Args:
            ilk: Collateral type
            urn: Identifies the vault holder or proxy
        """
        assert isinstance(ilk, Ilk)
        assert isinstance(urn, Urn)
        ilk = self.vat.ilk(ilk.name)
        urn = self.vat.urn(ilk, urn.address)
        rate = ilk.rate

        # Collateral value should be less than the product of our stablecoin debt and the debt multiplier
        safe = Ray(urn.ink) * ilk.spot >= Ray(urn.art) * rate
        if safe:
            return False

        # Ensure there's room in the litter box
        box: Rad = self.box()
        litter: Rad = self.litter()
        room: Rad = box - litter
        if litter >= box:
            logger.debug(f"biting {urn.address} would exceed maximum Dai out for liquidation")
            return False
        if room < ilk.dust:
            return False

        # Prevent null auction (ilk.dunk [Rad], ilk.rate [Ray], ilk.chop [Wad])
        dart: Wad = min(urn.art, Wad(min(self.dunk(ilk), room) / Rad(ilk.rate) / Rad(self.chop(ilk))))
        dink: Wad = min(urn.ink, urn.ink * dart / urn.art)

        return dart > Wad(0) and dink > Wad(0)

    def bite(self, ilk: Ilk, urn: Urn) -> Transact:
        """ Initiate liquidation of a vault, kicking off a flip auction

        Args:
            ilk: Identifies the type of collateral.
            urn: Address of the vault holder.
        """
        assert isinstance(ilk, Ilk)
        assert isinstance(urn, Urn)

        ilk = self.vat.ilk(ilk.name)
        urn = self.vat.urn(ilk, urn.address)
        rate = self.vat.ilk(ilk.name).rate
        logger.info(f'Biting {ilk.name} vault {urn.address.address} with ink={urn.ink} spot={ilk.spot} '
                    f'art={urn.art} rate={rate}')

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'bite', [ilk.toBytes(), urn.address.address])

    def chop(self, ilk: Ilk) -> Wad:
        assert isinstance(ilk, Ilk)

        (flip, chop, dunk) = self._contract.functions.ilks(ilk.toBytes()).call()
        return Wad(chop)

    def dunk(self, ilk: Ilk) -> Rad:
        assert isinstance(ilk, Ilk)

        (flip, chop, dunk) = self._contract.functions.ilks(ilk.toBytes()).call()
        return Rad(dunk)

    def flipper(self, ilk: Ilk) -> Address:
        assert isinstance(ilk, Ilk)

        (flip, chop, dunk) = self._contract.functions.ilks(ilk.toBytes()).call()
        return Address(flip)

    def box(self) -> Rad:
        return Rad(self._contract.functions.box().call())

    def litter(self) -> Rad:
        return Rad(self._contract.functions.litter().call())

    def past_bites(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogBite]:
        """Synchronously retrieve past LogBite events.

        `LogBite` events are emitted every time someone bites a CDP.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `LogBite` events represented as :py:class:`pymaker.dss.Cat.LogBite` class.
        """
        assert isinstance(number_of_past_blocks, int)
        assert isinstance(event_filter, dict) or (event_filter is None)

        return self._past_events(self._contract, 'Bite', Cat.LogBite, number_of_past_blocks, event_filter)

    def __repr__(self):
        return f"Cat('{self.address}')"


class Dog(Contract):
    """A client for the `Dog` contract, used to liquidate unsafe vaults.
    Specifically, this contract is useful for Clip auctions.

    Ref. <https://github.com/makerdao/dss/blob/master/src/dog.sol>
    """

    # This information is read from the `Bark` event emitted from `Dog.bark`
    class LogBark:
        def __init__(self, log):
            self.ilk = Ilk.fromBytes(log['args']['ilk'])
            self.urn = Urn(Address(log['args']['urn']))
            self.ink = Wad(log['args']['ink'])
            self.art = Wad(log['args']['art'])
            self.due = Rad(log['args']['due'])
            self.clip = Address(log['args']['clip'])
            self.id = int(log['args']['id'])
            self.raw = log

        def era(self, web3: Web3):
            return web3.eth.getBlock(self.raw['blockNumber'])['timestamp']

        def __eq__(self, other):
            assert isinstance(other, Cat.LogBite)
            return self.__dict__ == other.__dict__

        def __repr__(self):
            return pformat(vars(self))

    abi = Contract._load_abi(__name__, 'abi/Dog.abi')
    bin = Contract._load_bin(__name__, 'abi/Dog.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)
        self.vat = Vat(web3, Address(self._contract.functions.vat().call()))
        self.vow = Vow(web3, Address(self._contract.functions.vow().call()))

    def live(self) -> bool:
        return self._contract.functions.live().call() > 0

    def clipper(self, ilk: Ilk) -> Address:
        assert isinstance(ilk, Ilk)

        (clip, chop, hole, dirt) = self._contract.functions.ilks(ilk.toBytes()).call()
        return Address(clip)

    def chop(self, ilk: Ilk) -> Wad:
        assert isinstance(ilk, Ilk)
        (clip, chop, hole, dirt) = self._contract.functions.ilks(ilk.toBytes()).call()
        return Wad(chop)

    def hole(self, ilk: Ilk) -> Rad:
        assert isinstance(ilk, Ilk)
        (clip, chop, hole, dirt) = self._contract.functions.ilks(ilk.toBytes()).call()
        return Rad(hole)

    def dirt(self, ilk: Ilk) -> Rad:
        assert isinstance(ilk, Ilk)
        (clip, chop, hole, dirt) = self._contract.functions.ilks(ilk.toBytes()).call()
        return Rad(dirt)

    def dog_hole(self) -> Rad:
        return Rad(self._contract.functions.Hole().call())

    def dog_dirt(self) -> Rad:
        return Rad(self._contract.functions.Dirt().call())

    def bark(self, ilk: Ilk, urn: Urn, kpr: Address = None) -> Transact:
        """ Initiate liquidation of a vault, kicking off a flip auction

        Args:
            ilk: Identifies the type of collateral.
            urn: Address of the vault holder.
            kpr: Keeper address; leave empty to use web3 default.
        """
        assert isinstance(ilk, Ilk)
        assert isinstance(urn, Urn)
        if kpr:
            assert isinstance(kpr, Address)
        else:
            kpr = Address(self.web3.eth.defaultAccount)

        ilk = self.vat.ilk(ilk.name)
        urn = self.vat.urn(ilk, urn.address)
        rate = self.vat.ilk(ilk.name).rate
        logger.info(f'Barking {ilk.name} vault {urn.address.address} with ink={urn.ink} spot={ilk.spot} '
                    f'art={urn.art} rate={rate}')

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'bark', [ilk.toBytes(), urn.address.address, kpr.address])

    def past_barks(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogBark]:
        """Synchronously retrieve past LogBark events.

        `LogBark` events are emitted every time someone bites a vault.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `LogBark` events represented as :py:class:`pymaker.dss.Dog.LogBark` class.
        """
        assert isinstance(number_of_past_blocks, int)
        assert isinstance(event_filter, dict) or (event_filter is None)

        return self._past_events(self._contract, 'Bark', Dog.LogBark, number_of_past_blocks, event_filter)


class Pot(Contract):
    """A client for the `Pot` contract, which implements the DSR.

    Ref. <https://github.com/makerdao/dss/blob/master/src/pot.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/Pot.abi')
    bin = Contract._load_bin(__name__, 'abi/Pot.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def approve(self, source: Address, approval_function, **kwargs):
        """Approve the pot to access Dai from our Urns"""
        assert isinstance(source, Address)
        assert(callable(approval_function))

        approval_function(ERC20Token(web3=self.web3, address=source), self.address, self.__class__.__name__, **kwargs)

    def pie_of(self, address: Address) -> Wad:
        assert isinstance(address, Address)
        return Wad(self._contract.functions.pie(address.address).call())

    def pie(self) -> Wad:
        pie = self._contract.functions.Pie().call()
        return Wad(pie)

    def dsr(self) -> Ray:
        dsr = self._contract.functions.dsr().call()
        return Ray(dsr)

    def chi(self) -> Ray:
        chi = self._contract.functions.chi().call()
        return Ray(chi)

    def rho(self) -> datetime:
        rho = self._contract.functions.rho().call()
        return datetime.fromtimestamp(rho)

    def drip(self) -> Transact:
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'drip', [])

    """ Join/Exit in Pot can be invoked through pymaker/dsrmanager.py and pymaker/dsr.py """

    def __repr__(self):
        return f"Pot('{self.address}')"


class TokenFaucet(Contract):
    """A client for the `TokenFaucet` contract, to obtain ERC-20 tokens on testnets for testing purposes.

    Ref. <https://github.com/makerdao/token-faucet/blob/master/src/TokenFaucet.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/TokenFaucet.abi')
    bin = Contract._load_bin(__name__, 'abi/TokenFaucet.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def gulp(self, address: Address):
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'gulp(address)', [address.address])
