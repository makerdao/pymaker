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

    def __init__(self, name: str, take: Optional[Ray]=None,
                                  rate: Optional[Ray]=None,
                                  ink: Optional[Wad]=None,
                                  art: Optional[Wad]=None):
        assert (isinstance(name, str))
        assert (isinstance(take, Ray) or (take is None))
        assert (isinstance(rate, Ray) or (rate is None))
        assert (isinstance(ink, Wad) or (ink is None))
        assert (isinstance(art, Wad) or (art is None))

        self.name = name
        self.take = take
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
           and (self.take == other.take) \
           and (self.rate == other.rate) \
           and (self.ink == other.ink) \
           and (self.art == other.art)

    def __repr__(self):
        repr = ''
        if self.take:
            repr += f' take={self.take}'
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


class DaiAdapter(Contract):
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
                        'join', [urn.toBytes(), value.value])

    def exit(self, urn: Urn, value: Wad) -> Transact:
        assert isinstance(urn, Urn)
        assert isinstance(value, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'exit', [urn.toBytes(), value.value])


class DaiVat(Contract):
    """A client for the `DaiMove` contract.

    Ref. <https://github.com/makerdao/dss/blob/master/src/move.sol#L50>
    """

    abi = Contract._load_abi(__name__, 'abi/DaiMove.abi')
    bin = Contract._load_bin(__name__, 'abi/DaiMove.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @classmethod
    def deploy(cls, web3: Web3, vat: Address):
        return cls(web3=web3, address=Contract._deploy(web3, cls.abi, cls.bin, [vat.address]))

    def hope(self, guy: Address) -> Transact:
        assert isinstance(guy, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'hope', [guy.address])

    def move(self, src: Address, dst: Address, amount: Wad) -> Transact:
        assert isinstance(src, Address)
        assert isinstance(dst, Address)
        assert isinstance(amount, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'move', [src.address, dst.address, amount.value])


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
                        'join', [urn.toBytes(), value.value])

    def exit(self, urn: Urn, value: Wad) -> Transact:
        assert isinstance(urn, Urn)
        assert isinstance(value, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'exit', [urn.toBytes(), value.value])


class GemVat(Contract):
    """A client for the `GemMove` contract.

    Ref. <https://github.com/makerdao/dss/blob/master/src/move.sol#L25>
    """

    abi = Contract._load_abi(__name__, 'abi/GemMove.abi')
    bin = Contract._load_bin(__name__, 'abi/GemMove.bin')

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    @classmethod
    def deploy(cls, web3: Web3, vat: Address, ilk: Ilk, gem: Address):
        return cls(web3=web3, address=Contract._deploy(web3, cls.abi, cls.bin, [vat.address,
                                                                                ilk.toBytes()]))

    def ilk(self):
        return Ilk.fromBytes(self._contract.call().ilk())


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

    def rely(self, guy: Address) -> Transact:
        assert isinstance(guy, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'rely', [guy.address])

    def init(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'init', [ilk.toBytes()])

    def ilk(self, name: str) -> Ilk:
        assert isinstance(name, str)

        b32_ilk = Ilk(name).toBytes()
        (take, rate, ink, art) = self._contract.call().ilks(b32_ilk)

        return Ilk(name, Ray(take), Ray(rate), Wad(ink), Wad(art))

    def gem(self, ilk: Ilk, urn: Address) -> Rad:
        assert isinstance(ilk, Ilk)
        assert isinstance(urn, Address)

        return Rad(self._contract.call().gem(ilk.toBytes(), Urn(urn).toBytes()))

    def dai(self, urn: Address) -> Rad:
        assert isinstance(urn, Address)

        return Rad(self._contract.call().dai(Urn(urn).toBytes()))

    def urn(self, ilk: Ilk, address: Address) -> Urn:
        assert isinstance(ilk, Ilk)
        assert isinstance(address, Address)

        (ink, art) = self._contract.call().urns(ilk.toBytes(), Urn(address).toBytes())
        return Urn(address, ilk, Wad(ink), Wad(art))

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
        self.mover: GemVat = None
        self.flipper: Flipper = None
        self.pip = None
        self.spotter: Spotter = None

    @staticmethod
    def deploy(web3: Web3, name: str, vat: Vat):
        collateral = Collateral(Ilk(name))
        collateral.gem = DSToken.deploy(web3=web3, symbol=name)
        collateral.adapter = GemAdapter.deploy(web3=web3, vat=vat.address,
                                               ilk=collateral.ilk, gem=collateral.gem.address)
        collateral.mover = GemVat.deploy(web3=web3, vat=vat.address,
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
    def deploy(web3: Web3, pit: Address, ilk: Ilk):
        assert isinstance(web3, Web3)
        assert isinstance(pit, Address)
        assert isinstance(ilk, Ilk)

        return Spotter(web3=web3, address=Contract._deploy(web3, Spotter.abi, Spotter.bin, [pit.address,
                                                                                            ilk.toBytes()]))

    def file_pip(self, pip: Address) -> Transact:
        assert isinstance(pip, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'file(address)', [pip.address])

    def file_mat(self, mat: Ray) -> Transact:
        assert isinstance(mat, Ray)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'file(uint256)', [mat.value])

    def mat(self) -> Ray:
        return Ray(self._contract.call().mat())

    def poke(self) -> Transact:
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'poke', [])

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


class Drip(Contract):
    """A client for the `Drip` contract.

    Ref. <https://github.com/makerdao/dss/blob/master/src/drip.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/Drip.abi')
    bin = Contract._load_bin(__name__, 'abi/Drip.bin')

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

        return Drip(web3=web3, address=Contract._deploy(web3, Drip.abi, Drip.bin, [vat.address]))

    def init(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'init', [ilk.toBytes()])

    def drip(self, ilk: Ilk) -> Transact:
        assert isinstance(ilk, Ilk)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'drip', [ilk.toBytes()])

    def file_vow(self, vow: Vow) -> Transact:
        assert isinstance(vow, Vow)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,bytes32)', [Web3.toBytes(text="vow"), Urn(vow.address).toBytes()])

    def file_tax(self, ilk: Ilk, tax: Ray) -> Transact:
        assert isinstance(ilk, Ilk)
        assert isinstance(tax, Ray)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,bytes32,uint256)',
                        [ilk.toBytes(), Web3.toBytes(text="tax"), tax.value])

    def vat(self) -> Address:
        return Address(self._contract.call().vat())

    def vow(self) -> Urn:
        return Urn.fromBytes(self._contract.call().vow())

    def repo(self) -> Wad:
        return Wad(self._contract.call().repo())

    def tax(self, ilk: Ilk) -> Ray:
        assert isinstance(ilk, Ilk)

        return Ray(self._contract.call().ilks(ilk.toBytes())[0])

    def rho(self, ilk: Ilk) -> int:
        assert isinstance(ilk, Ilk)

        return Web3.toInt(self._contract.call().ilks(ilk.toBytes())[1])

    def __repr__(self):
        return f"Drip('{self.address}')"


class Pit(Contract):
    """A client for the `Pit` contract.

    Ref. <https://github.com/makerdao/dss/blob/master/src/frob.sol>
    """

    abi = Contract._load_abi(__name__, 'abi/Pit.abi')
    bin = Contract._load_bin(__name__, 'abi/Pit.bin')

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

        return Pit(web3=web3, address=Contract._deploy(web3, Pit.abi, Pit.bin, [vat.address]))

    def rely(self, guy: Address) -> Transact:
        assert isinstance(guy, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'rely', [guy.address])

    def file_global_line(self, ceiling: Wad) -> Transact:
        assert isinstance(ceiling, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,uint256)', [Web3.toBytes(text="Line"), ceiling.value])

    def file_line(self, ilk: Ilk, ceiling: Wad) -> Transact:
        assert isinstance(ilk, Ilk)
        assert isinstance(ceiling, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,bytes32,uint256)', [ilk.toBytes(), Web3.toBytes(text="line"), ceiling.value])

    def frob(self, ilk: Ilk, dink: Wad, dart: Wad):
        assert isinstance(ilk, Ilk)
        assert isinstance(dink, Wad)
        assert isinstance(dart, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'frob', [ilk.toBytes(), dink.value, dart.value])

    def spot(self, ilk: Ilk) -> Ray:
        assert isinstance(ilk, Ilk)

        (spot, line) = self._contract.call().ilks(ilk.toBytes())
        return Ray(spot)

    def line(self, ilk: Ilk) -> Wad:
        assert isinstance(ilk, Ilk)

        (spot, line) = self._contract.call().ilks(ilk.toBytes())
        return Wad(line)

    def global_line(self) -> Wad:
        return Wad(self._contract.call().Line())

    def past_frob(self, number_of_past_blocks: int, event_filter: dict = None) -> List[LogFrob]:
        """Synchronously retrieve past LogFrob events.

        `LogFrob` events are emitted every time someone frob a CDP.

        Args:
            number_of_past_blocks: Number of past Ethereum blocks to retrieve the events from.
            event_filter: Filter which will be applied to returned events.

        Returns:
            List of past `LogFrob` events represented as :py:class:`pymake.dss.LogFrob` class.
        """
        assert isinstance(number_of_past_blocks, int)
        assert isinstance(event_filter, dict) or (event_filter is None)

        return self._past_events(self._contract, 'Frob', LogFrob, number_of_past_blocks, event_filter)

    def __repr__(self):
        return f"Pit('{self.address}')"


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
        urn = Urn.fromBytes(flip_urn)
        urn.ilk = Ilk.fromBytes(flip_ilk)
        urn.ink = Wad(flip_ink)
        return Cat.Flip(id, urn, Wad(flip_tab))

    def bite(self, ilk: Ilk, urn: Urn):
        assert isinstance(ilk, Ilk)
        assert isinstance(urn, Urn)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'bite', [ilk.toBytes(), urn.toBytes()])

    def flip(self, flip: Flip, amount: Wad):
        assert isinstance(flip, Cat.Flip)
        assert isinstance(amount, Wad)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'flip', [flip.id, amount.value])

    def file_vow(self, vow: Vow) -> Transact:
        assert isinstance(vow, Vow)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,address)', [Web3.toBytes(text="vow"), vow.address.address])

    def file_pit(self, pit: Pit) -> Transact:
        assert isinstance(pit, Pit)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,address)', [Web3.toBytes(text="pit"), pit.address.address])

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

    def pit(self) -> Address:
        return Address(self._contract.call().pit())

    def vat(self) -> Address:
        return Address(self._contract.call().vat())

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
