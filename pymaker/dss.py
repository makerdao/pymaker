# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2018 bargst
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
from pprint import pformat
from typing import Optional, List

from hexbytes import HexBytes
from web3 import Web3
from web3.utils.events import get_event_data

from pymaker import Address, Contract, Transact
from pymaker.auctions import Flapper, Flipper, Flopper
from pymaker.token import DSToken
from pymaker.numeric import Wad, Ray, Rad


class Ilk:
    """The `Ilk` object as a type of collateral.
    """

    def __init__(self, name: str, rate: Optional[Ray]=None,
                                  ink: Optional[Wad]=None,
                                  art: Optional[Wad]=None):
        assert (isinstance(name, str))
        assert (isinstance(rate, Ray) or (rate is None))
        assert (isinstance(ink, Wad) or (ink is None))
        assert (isinstance(art, Wad) or (art is None))

        self.name = name
        self.rate = rate
        self.ink = ink
        self.art = art

    def toBytes(self):
        return Web3.toBytes(text=self.name).ljust(32, bytes(1))

    @staticmethod
    def fromBytes(ilk: bytes):
        assert (isinstance(ilk, bytes))

        name = Web3.toText(ilk.strip(bytes(1)))
        return Ilk(name)

    def __eq__(self, other):
        assert isinstance(other, Ilk)

        return (self.name == other.name) \
           and (self.rate == other.rate) \
           and (self.ink == other.ink) \
           and (self.art == other.art)

    def __repr__(self):
        repr = ''
        if self.rate:
            repr += f' rate={self.rate}'
        if self.ink:
            repr += f' Ink={self.ink}'
        if self.art:
            repr += f' Art={self.art}'
        if repr:
            repr = f'[{repr.strip()}]'

        return f"Ilk('{self.name}'){repr}"


class Urn:
    """The `Urn` object as a CDP for a single collateral
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


class LogBite:
    def __init__(self, log):
        self.ilk = Ilk.fromBytes(log['args']['ilk'])
        self.urn = Urn.fromBytes(log['args']['urn'])
        self.ink = Wad(log['args']['ink'])
        self.art = Wad(log['args']['art'])
        self.tab = Wad(log['args']['tab'])
        self.flip = int(log['args']['flip'])
        self.iInk = Wad(log['args']['iInk'])
        self.iart = Wad(log['args']['iArt'])
        self.raw = log

    @classmethod
    def from_event(cls, event: dict):
        assert isinstance(event, dict)

        topics = event.get('topics')
        if topics and topics[0] == HexBytes('0x99b5620489b6ef926d4518936cfec15d305452712b88bd59da2d9c10fb0953e8'):
            log_bite_abi = [abi for abi in Cat.abi if abi.get('name') == 'Bite'][0]
            event_data = get_event_data(log_bite_abi, event)

            return LogBite(event_data)
        else:
            logging.warning(f'[from_event] Invalid topic in {event}')

    def era(self, web3: Web3):
        return web3.eth.getBlock(self.raw['blockNumber'])['timestamp']

    def __eq__(self, other):
        assert isinstance(other, LogBite)
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return pformat(vars(self))


class LogFrob:
    def __init__(self, log):
        self.ilk = Ilk.fromBytes(log['args']['ilk'])
        self.urn = Urn.fromBytes(log['args']['urn'])
        self.ink = Wad(log['args']['ink'])
        self.art = Wad(log['args']['art'])
        self.dink = Wad(log['args']['dink'])
        self.dart = Wad(log['args']['dart'])
        self.iink = Wad(log['args']['iInk'])
        self.iart = Wad(log['args']['iArt'])
        self.raw = log

    @classmethod
    def from_event(cls, event: dict):
        assert isinstance(event, dict)

        topics = event.get('topics')
        if topics and topics[0] == HexBytes('0xb2afa28318bcc689926b52835d844de174ef8de97e982a85c0199d584920791b'):
            log_frob_abi = [abi for abi in Pit.abi if abi.get('name') == 'Frob'][0]
            event_data = get_event_data(log_frob_abi, event)

            return LogFrob(event_data)
        else:
            logging.warning(f'[from_event] Invalid topic in {event}')

    def era(self, web3: Web3):
        return web3.eth.getBlock(self.raw['blockNumber'])['timestamp']

    def __eq__(self, other):
        assert isinstance(other, LogFrob)
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return pformat(vars(self))


class LogNote(LogFrob):

    @classmethod
    def from_event(cls, event: dict):
        assert isinstance(event, dict)

        topics = event.get('topics')
    # TODO
    # handle Note event, return LogNote object

    def __eq__(self, other):
        assert isinstance(other, LogNote)
        return self.__dict__ == other.__dict__


class DaiJoin(Contract):
    """A client for the `DaiJoin` contract.

    Ref. <https://github.com/makerdao/dss/blob/master/src/join.sol#L81>
    """

    abi = Contract._load_abi(__name__, 'abi/DaiJoin.abi')
    bin = Contract._load_bin(__name__, 'abi/DaiJoin.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @classmethod
    def deploy(cls, web3: Web3, vat: Address, dai: Address):
        return cls(web3=web3, address=Contract._deploy(web3, cls.abi, cls.bin, [vat.address, dai.address]))

    def join(self, urn: Urn, value: Wad) -> Transact:
        assert isinstance(urn, Urn)
        assert isinstance(value, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'join', [urn.address, value.value])

    def exit(self, urn: Urn, value: Wad) -> Transact:
        assert isinstance(urn, Urn)
        assert isinstance(value, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'exit', [urn.address, value.value])


class GemAdapter(Contract):
    """A client for the `GemJoin` contract.

    Ref. <https://github.com/makerdao/dss/blob/master/src/join.sol#L34>
    """

    abi = Contract._load_abi(__name__, 'abi/GemJoin.abi')
    bin = Contract._load_bin(__name__, 'abi/GemJoin.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @classmethod
    def deploy(cls, web3: Web3, vat: Address, ilk: Ilk, gem: Address):
        return cls(web3=web3, address=Contract._deploy(web3, cls.abi, cls.bin, [vat.address,
                                                                                ilk.toBytes(),
                                                                                gem.address]))

    def ilk(self):
        return Ilk.fromBytes(self._contract.call().ilk())

    def join(self, urn: Urn, value: Wad) -> Transact:
        assert isinstance(urn, Urn)
        assert isinstance(value, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'join', [urn.address.address, value.value])

    def exit(self, usr: Address, value: Wad) -> Transact:
        assert isinstance(usr, Address)
        assert isinstance(value, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'exit', [usr.Address, value.value])


class Vat(Contract):
    """A client for the `Vat` contract.

    Ref. <https://github.com/makerdao/dss/blob/master/src/tune.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/Vat.abi')
    bin = Contract._load_bin(__name__, 'abi/Vat.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3):
        assert isinstance(web3, Web3)

        return Vat(web3=web3, address=Contract._deploy(web3, Vat.abi, Vat.bin, []))

    def rely(self, usr: Address) -> Transact:
        assert isinstance(usr, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'rely', [usr.address])

    def init(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'init', [ilk.toBytes()])

    def file_line(self, ilk: Ilk, amount: Wad) -> Transact:
        assert isinstance(amount, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,bytes32,uint256)', [ilk.toBytes(), Web3.toBytes(text="line"), amount.value])

    def ilk(self, name: str) -> Ilk:
        assert isinstance(name, str)

        b32_ilk = Ilk(name).toBytes()
        (art, rate, spot, line, dust) = self._contract.call().ilks(b32_ilk)

        # TODO: We could get "ink" from the urn, but caller must provide an address.
        return Ilk(name, rate=Ray(rate), ink=Wad(0), art=Wad(art))

    def gem(self, ilk: Ilk, urn: Address) -> Rad:
        assert isinstance(ilk, Ilk)
        assert isinstance(urn, Address)

        return Rad(self._contract.call().gem(ilk.toBytes(), urn.address))

    def dai(self, urn: Address) -> Rad:
        assert isinstance(urn, Address)

        return Rad(self._contract.call().dai(Urn(urn).toBytes()))

    def urn(self, ilk: Ilk, address: Address) -> Urn:
        assert isinstance(ilk, Ilk)
        assert isinstance(address, Address)

        (ink, art) = self._contract.call().urns(ilk.toBytes(), address.address)
        return Urn(address, ilk, Wad(ink), Wad(art))

    def spot(self, ilk: Ilk) -> Ray:
        assert isinstance(ilk, Ilk)

        (art, rate, spot, line) = self._contract.call().ilks(ilk.toBytes())
        return Ray(spot)

    def line(self, ilk: Ilk) -> Wad:
        assert isinstance(ilk, Ilk)

        (art, rate, spot, line) = self._contract.call().ilks(ilk.toBytes())
        return Wad(line)

    def frob(self, ilk: Ilk, address: Address, dink: Wad, dart: Wad, collateral_owner=None, dai_recipient=None):
        assert isinstance(ilk, Ilk)
        assert isinstance(address, Address)
        assert isinstance(dink, Wad)
        assert isinstance(dart, Wad)
        assert isinstance(collateral_owner, Address) or (collateral_owner is None)
        assert isinstance(dai_recipient, Address) or (dai_recipient is None)

        # Usually these addresses are the same as the account holding the urn
        v = collateral_owner or address
        w = dai_recipient or address
        assert isinstance(v, Address)
        assert isinstance(w, Address)

        # FIXME: need to debug vat.sol
        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'frob', [ilk.toBytes(), address.address, v.address, w.address, dink.value, dart.value])

    def past_note(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogNote]:
        """Synchronously retrieve past LogNote events.
         Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.
         Returns:
            List of past `LogNote` events represented as :py:class:`pymake.dss.LogNote` class.
        """
        assert isinstance(number_of_past_blocks, int)
        assert isinstance(event_filter, dict) or (event_filter is None)

        return self._past_events(self._contract, 'Note', LogNote, number_of_past_blocks, event_filter)

    def __eq__(self, other):
        assert isinstance(other, Vat)
        return self.address == other.address

    def __repr__(self):
        return f"Vat('{self.address}')"


class Collateral:
    """The `Collateral` object as a wrapping class for collateral properties.
    """

    def __init__(self, ilk: Ilk):
        assert isinstance(ilk, Ilk)

        self.ilk = ilk
        self.gem: DSToken = None
        self.adapter: GemAdapter = None
        self.flipper: Flipper = None
        self.pip = None
        self.spotter: Spotter = None

    @staticmethod
    def deploy(web3: Web3, name: str, vat: Vat, decimals=18):
        collateral = Collateral(Ilk(name))
        collateral.gem = DSToken.deploy(web3=web3, symbol=name)
        # TODO: Set decimals on the DSToken
        collateral.adapter = GemAdapter.deploy(web3=web3, vat=vat.address,
                                               ilk=collateral.ilk, gem=collateral.gem.address)

        return collateral


class Spotter(Contract):
    """A client for the `Spotter` contract.

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

    @staticmethod
    def deploy(web3: Web3, vat: Address):
        assert isinstance(web3, Web3)
        assert isinstance(vat, Address)

        return Spotter(web3=web3, address=Contract._deploy(web3, Spotter.abi, Spotter.bin, [vat.address]))

    def file_pip(self, ilk: Ilk, pip: Address) -> Transact:
        assert isinstance(ilk, Ilk)
        assert isinstance(pip, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'file(bytes32,address)',
                        [ilk.toBytes(), pip.address])

    def file_par(self, par: Ray) -> Transact:
        assert isinstance(par, Ray)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'file(bytes32,uint256)',
                        [Web3.toBytes(text="par"), par.value])

    def file_mat(self, ilk: Ilk, mat: Ray) -> Transact:
        assert isinstance(ilk, Ilk)
        assert isinstance(mat, Ray)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'file(bytes32,bytes32,uint256)',
                        [ilk.toBytes(), Web3.toBytes(text="mat"), mat.value])

    def poke(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'poke', [ilk.toBytes()])

    def vat(self) -> Address:
        return Address(self._contract.call().vat())

    def par(self) -> Ray:
        return Ray(self._contract.call().par())

    def __repr__(self):
        return f"Spotter('{self.address}')"


class Vow(Contract):
    """A client for the `Vow` contract.

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

    @staticmethod
    def deploy(web3: Web3):
        assert isinstance(web3, Web3)

        return Vow(web3=web3, address=Contract._deploy(web3, Vow.abi, Vow.bin, []))

    def rely(self, guy: Address) -> Transact:
        assert isinstance(guy, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'rely', [guy.address])

    def file_vat(self, vat: Vat) -> Transact:
        assert isinstance(vat, Vat)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,address)', [Web3.toBytes(text="vat"), vat.address.address])

    def file_flap(self, flap: Flapper) -> Transact:
        assert isinstance(flap, Flapper)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,address)', [Web3.toBytes(text="flap"), flap.address.address])

    def file_flop(self, flop: Flopper) -> Transact:
        assert isinstance(flop, Flopper)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,address)', [Web3.toBytes(text="flop"), flop.address.address])

    def file_bump(self, amount: Wad) -> Transact:
        assert isinstance(amount, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,uint256)', [Web3.toBytes(text="bump"), amount.value])

    def file_sump(self, amount: Wad) -> Transact:
        assert isinstance(amount, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,uint256)', [Web3.toBytes(text="sump"), amount.value])

    def vat(self) -> Address:
        return Address(self._contract.call().vat())

    def flapper(self) -> Address:
        return Address(self._contract.call().cow())

    def flopper(self) -> Address:
        return Address(self._contract.call().row())

    def sin(self) -> Wad:
        return Wad(self._contract.call().Sin())

    def sin_of(self, era: int) -> Wad:
        return Wad(self._contract.call().sin(era))

    def woe(self) -> Wad:
        return Wad(self._contract.call().Woe())

    def ash(self) -> Wad:
        return Wad(self._contract.call().Ash())

    def joy(self) -> Wad:
        return Wad(self._contract.call().Joy())

    def awe(self) -> Wad:
        return Wad(self._contract.call().Awe())

    def wait(self) -> int:
        return int(self._contract.call().wait())

    def sump(self) -> Wad:
        return Wad(self._contract.call().sump())

    def bump(self) -> Wad:
        return Wad(self._contract.call().bump())

    def hump(self) -> Wad:
        return Wad(self._contract.call().hump())

    def flog(self, era: int) -> Transact:
        assert isinstance(era, int)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'flog', [era])

    def heal(self, wad: Wad) -> Transact:
        assert isinstance(wad, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'heal', [wad.value])

    def kiss(self, wad: Wad) -> Transact:
        assert isinstance(wad, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kiss', [wad.value])

    def flop(self) -> Transact:
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'flop', [])

    def flap(self) -> Transact:
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'flap', [])

    def __repr__(self):
        return f"Vow('{self.address}')"


class Jug(Contract):
    """A client for the `Jug` contract.

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

    @staticmethod
    def deploy(web3: Web3, vat: Address):
        assert isinstance(web3, Web3)
        assert isinstance(vat, Address)

        return Jug(web3=web3, address=Contract._deploy(web3, Jug.abi, Jug.bin, [vat.address]))

    def init(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'init', [ilk.toBytes()])

    def drip(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'drip', [ilk.toBytes()])

    def file_duty(self, ilk: Ilk, duty: Ray) -> Transact:
        assert isinstance(ilk, Ilk)
        assert isinstance(duty, Ray)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,bytes32,uint256)',
                        [ilk.toBytes(), Web3.toBytes(text="duty"), duty.value])

    def file_base(self, base: Ray) -> Transact:
        assert isinstance(base, Ray)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,uint256)',
                        [Web3.toBytes("base"), base.value])

    def file_vow(self, vow: Vow) -> Transact:
        assert isinstance(vow, Vow)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,address)', [Web3.toBytes(text="vow"), vow.address.address])

    def vat(self) -> Address:
        return Address(self._contract.call().vat())

    def vow(self) -> Address:
        return Address(self._contract.call().vow())

    def base(self) -> Wad:
        return Wad(self._contract.call().base())

    def duty(self, ilk: Ilk) -> Ray:
        assert isinstance(ilk, Ilk)

        return Ray(self._contract.call().ilks(ilk.toBytes())[0])

    def rho(self, ilk: Ilk) -> int:
        assert isinstance(ilk, Ilk)

        return Web3.toInt(self._contract.call().ilks(ilk.toBytes())[1])

    def __repr__(self):
        return f"Jug('{self.address}')"


class Cat(Contract):
    """A client for the `Cat` contract.

    Ref. <https://github.com/makerdao/dss/blob/master/src/bite.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/Cat.abi')
    bin = Contract._load_bin(__name__, 'abi/Cat.bin')

    class Flip:
        def __init__(self, id: int, urn: Urn, tab: Wad):
            assert isinstance(id, int)
            assert isinstance(urn, Urn)
            assert isinstance(tab, Wad)

            self.id = id
            self.urn = urn
            self.tab = tab

        def __repr__(self):
            return f"Cat.Flip('{self.id}')[tab={self.tab} urn={self.urn}]"

        def __eq__(self, other):
            assert isinstance(other, Cat.Flip)

            return self.id == other.id and self.urn.address == other.urn.address and self.tab == other.tab

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @staticmethod
    def deploy(web3: Web3, vat: Address):
        assert isinstance(web3, Web3)
        assert isinstance(vat, Address)

        return Cat(web3=web3, address=Contract._deploy(web3, Cat.abi, Cat.bin, [vat.address]))

    def nflip(self):
        return int(self._contract.call().nflip())

    def flips(self, id: int) -> Flip:
        assert isinstance(id, int)

        (flip_ilk, flip_urn, flip_ink, flip_tab) = self._contract.call().flips(id)
        urn = Urn(address=Address(flip_urn), ilk=Ilk.fromBytes(flip_ilk), ink=Wad(flip_ink))
        return Cat.Flip(id, urn, Wad(flip_tab))

    def bite(self, ilk: Ilk, urn: Urn):
        assert isinstance(ilk, Ilk)
        assert isinstance(urn, Urn)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'bite', [ilk.toBytes(), urn.address])

    def flip(self, flip: Flip, amount: Wad):
        assert isinstance(flip, Cat.Flip)
        assert isinstance(amount, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'flip', [flip.id, amount.value])

    def file_vow(self, vow: Vow) -> Transact:
        assert isinstance(vow, Vow)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,address)', [Web3.toBytes(text="vow"), vow.address.address])

    def file_flip(self, ilk: Ilk, flipper: Flipper) -> Transact:
        assert isinstance(ilk, Ilk)
        assert isinstance(flipper, Flipper)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,bytes32,address)',
                        [ilk.toBytes(), Web3.toBytes(text="flip"), flipper.address.address])

    def file_lump(self, ilk: Ilk, lump: Wad) -> Transact:
        assert isinstance(ilk, Ilk)
        assert isinstance(lump, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,bytes32,uint256)', [ilk.toBytes(), Web3.toBytes(text="lump"), lump.value])

    def file_chop(self, ilk: Ilk, chop: Ray) -> Transact:
        assert isinstance(ilk, Ilk)
        assert isinstance(chop, Ray)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,bytes32,uint256)', [ilk.toBytes(), Web3.toBytes(text="chop"), chop.value])

    def lump(self, ilk: Ilk) -> Wad:
        assert isinstance(ilk, Ilk)

        (flip, chop, lump) = self._contract.call().ilks(ilk.toBytes())
        return Wad(lump)

    def flipper(self, ilk: Ilk) -> Address:
        assert isinstance(ilk, Ilk)

        (flip, chop, lump) = self._contract.call().ilks(ilk.toBytes())
        return Address(flip)

    def vat(self) -> Address:
        return Address(self._contract.call().vat())

    def vow(self) -> Address:
        return Address(self._contract.call().vow())

    def past_bite(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogBite]:
        """Synchronously retrieve past LogBite events.

        `LogBite` events are emitted every time someone bite a CDP.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `LogBite` events represented as :py:class:`pymake.dss.LogBite` class.
        """
        assert isinstance(number_of_past_blocks, int)
        assert isinstance(event_filter, dict) or (event_filter is None)

        return self._past_events(self._contract, 'Bite', LogBite, number_of_past_blocks, event_filter)

    def __repr__(self):
        return f"Cat('{self.address}')"
