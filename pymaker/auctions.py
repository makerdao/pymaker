# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2018-2019 reverendus, bargst, EdNoepel
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

from datetime import datetime
from pprint import pformat
from pymaker.numeric import Ray
from web3 import Web3

from pymaker import Contract, Address, Transact
from pymaker.numeric import Wad, Rad
from pymaker.token import ERC20Token


def toBytes(string: str):
    assert(isinstance(string, str))
    return string.encode('utf-8').ljust(32, bytes(1))


class AuctionContract(Contract):
    def __init__(self, web3: Web3, address: Address, abi: list, bids: callable):
        if self.__class__ == AuctionContract:
            raise NotImplemented('Abstract class; please call Flipper, Flapper, or Flopper ctor')
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)
        assert isinstance(abi, list)

        self.web3 = web3
        self.address = address
        self.abi = abi
        self._contract = self._get_contract(web3, abi, address)
        self._bids = bids

    def wards(self, address: Address) -> bool:
        assert isinstance(address, Address)

        return bool(self._contract.call().wards(address.address))

    def active_auctions(self) -> list:
        active_auctions = []
        auction_count = self.kicks()+1
        for index in range(1, auction_count):
            bid = self._bids(index)
            if bid.guy != Address("0x0000000000000000000000000000000000000000"):
                now = datetime.now().timestamp()
                if (bid.tic == 0 or now < bid.tic) and now < bid.end:
                    active_auctions.append(bid)
            index += 1
        return active_auctions

    def file_beg(self, beg: Ray) -> Transact:
        assert isinstance(beg, Ray)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,uint256)',
                        [Web3.toBytes(text="beg"), beg.value])

    def file_ttl(self, ttl: int) -> Transact:
        assert isinstance(ttl, int)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,uint256)',
                        [Web3.toBytes(text="ttl"), ttl])

    def file_tau(self, tau: int) -> Transact:
        assert isinstance(tau, int)

        return Transact(self, self.web3, self.abi, self.address, self._contract,
                        'file(bytes32,uint256)',
                        [Web3.toBytes(text="tau"), tau])

    def beg(self) -> Ray:
        """Returns the percentage minimum bid increase.

        Returns:
            The percentage minimum bid increase.
        """
        return Ray(self._contract.call().beg())

    def ttl(self) -> int:
        """Returns the bid lifetime.

        Returns:
            The bid lifetime (in seconds).
        """
        return int(self._contract.call().ttl())

    def tau(self) -> int:
        """Returns the total auction length.

        Returns:
            The total auction length (in seconds).
        """
        return int(self._contract.call().tau())

    def kicks(self) -> int:
        """Returns the number of auctions started so far.

        Returns:
            The number of auctions started so far.
        """
        return int(self._contract.call().kicks())


class Flipper(AuctionContract):
    """A client for the `Flipper` contract, TODO.

    You can find the source code of the `Flipper` contract here:
    <https://github.com/makerdao/dss/blob/master/src/flip.sol>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Flipper` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/Flipper.abi')
    bin = Contract._load_bin(__name__, 'abi/Flipper.bin')

    class Bid:
        def __init__(self, bid: Rad, lot: Wad, guy: Address, tic: int, end: int, urn: Address, gal: Address, tab: Rad):
            assert(isinstance(bid, Rad))
            assert(isinstance(lot, Wad))
            assert(isinstance(guy, Address))
            assert(isinstance(tic, int))
            assert(isinstance(end, int))
            assert(isinstance(urn, Address))
            assert(isinstance(gal, Address))
            assert(isinstance(tab, Rad))

            self.bid = bid
            self.lot = lot
            self.guy = guy
            self.tic = tic
            self.end = end
            self.urn = urn
            self.gal = gal
            self.tab = tab

        def __repr__(self):
            return f"Flipper.Bid({pformat(vars(self))})"

    @staticmethod
    def deploy(web3: Web3, vat: Address, ilk):
        assert(isinstance(vat, Address))
        assert(isinstance(ilk, bytes))

        return Flipper(web3=web3, address=Contract._deploy(web3, Flipper.abi, Flipper.bin, [vat.address, ilk]))

    def __init__(self, web3: Web3, address: Address):
        super(Flipper, self).__init__(web3, address, Flipper.abi, self.bids)

    def approve(self, approval_function, **kwargs):
        """Approve the `Flipper` to access our `dai` so we can participate in auctions.

        For available approval functions (i.e. approval modes) see `directly` and `via_tx_manager`
        in `pymaker.approval`.

        Args:
            approval_function: Approval function (i.e. approval mode).
        """
        assert(callable(approval_function))

        approval_function(token=ERC20Token(web3=self.web3, address=self.vat()),
                          spender_address=self.address, spender_name='Flipper', **kwargs)

    def vat(self) -> Address:
        """Returns the `vat` address.
         Returns:
            The address of the `vat` contract.
        """
        return Address(self._contract.call().vat())

    def bids(self, id: int) -> Bid:
        """Returns the auction details.

        Args:
            id: Auction identifier.

        Returns:
            The auction details.
        """
        assert(isinstance(id, int))

        array = self._contract.call().bids(id)

        return Flipper.Bid(bid=Rad(array[0]),
                           lot=Wad(array[1]),
                           guy=Address(array[2]),
                           tic=int(array[3]),
                           end=int(array[4]),
                           urn=Address(array[5]),
                           gal=Address(array[6]),
                           tab=Rad(array[7]))

    def kick(self, urn: Address, gal: Address, tab: Rad, lot: Wad, bid: Rad) -> Transact:
        assert(isinstance(urn, Address))
        assert(isinstance(gal, Address))
        assert(isinstance(tab, Rad))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Rad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kick', [urn.address,
                                                                                          gal.address,
                                                                                          tab.value,
                                                                                          lot.value,
                                                                                          bid.value])

    def tend(self, id: int, lot: Wad, bid: Rad) -> Transact:
        assert(isinstance(id, int))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Rad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'tend', [id, lot.value, bid.value])

    def dent(self, id: int, lot: Wad, bid: Rad) -> Transact:
        assert(isinstance(id, int))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Rad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'dent', [id, lot.value, bid.value])

    def deal(self, id: int) -> Transact:
        assert(isinstance(id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'deal', [id])

    def __repr__(self):
        return f"Flipper('{self.address}')"


class Flapper(AuctionContract):
    """A client for the `Flapper` contract, TODO.

    You can find the source code of the `Flapper` contract here:
    <https://github.com/makerdao/dss/blob/master/src/flap.sol>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Flapper` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/Flapper.abi')
    bin = Contract._load_bin(__name__, 'abi/Flapper.bin')

    class Bid:
        def __init__(self, bid: Wad, lot: Rad, guy: Address, tic: int, end: int, gal: Address):
            assert(isinstance(bid, Wad))        # MKR
            assert(isinstance(lot, Rad))        # DAI
            assert(isinstance(guy, Address))
            assert(isinstance(tic, int))
            assert(isinstance(end, int))
            assert(isinstance(gal, Address))

            self.bid = bid
            self.lot = lot
            self.guy = guy
            self.tic = tic
            self.end = end
            self.gal = gal

        def __repr__(self):
            return f"Flapper.Bid({pformat(vars(self))})"

    @staticmethod
    def deploy(web3: Web3, dai: Address, gem: Address):
        assert(isinstance(dai, Address))
        assert(isinstance(gem, Address))

        return Flapper(web3=web3, address=Contract._deploy(web3, Flapper.abi, Flapper.bin, [dai.address, gem.address]))

    def __init__(self, web3: Web3, address: Address):
        super(Flapper, self).__init__(web3, address, Flapper.abi, self.bids)

    def live(self) -> bool:
        return self._contract.call().live() > 0

    def approve(self, approval_function):
        """Approve the `Flapper` to access our `gem` so we can participate in auctions.

        For available approval functions (i.e. approval modes) see `directly` and `via_tx_manager`
        in `pymaker.approval`.

        Args:
            approval_function: Approval function (i.e. approval mode).
        """
        assert(callable(approval_function))

        approval_function(ERC20Token(web3=self.web3, address=self.gem()), self.address, 'Flapper')

    def gem(self) -> Address:
        """Returns the `gem` token.

        Returns:
            The address of the `gem` token.
        """
        return Address(self._contract.call().gem())

    def bids(self, id: int) -> Bid:
        """Returns the auction details.

        Args:
            id: Auction identifier.

        Returns:
            The auction details.
        """
        assert(isinstance(id, int))

        array = self._contract.call().bids(id)

        return Flapper.Bid(bid=Wad(array[0]),
                           lot=Rad(array[1]),
                           guy=Address(array[2]),
                           tic=int(array[3]),
                           end=int(array[4]),
                           gal=Address(array[5]))

    def kick(self, gal: Address, lot: Rad, bid: Wad) -> Transact:
        assert(isinstance(gal, Address))
        assert(isinstance(lot, Rad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kick', [gal.address,
                                                                                          lot.value,
                                                                                          bid.value])

    def tend(self, id: int, lot: Rad, bid: Wad) -> Transact:
        assert(isinstance(id, int))
        assert(isinstance(lot, Rad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'tend', [id, lot.value, bid.value])

    def deal(self, id: int) -> Transact:
        assert(isinstance(id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'deal', [id])

    def __repr__(self):
        return f"Flapper('{self.address}')"


class Flopper(AuctionContract):
    """A client for the `Flopper` contract, TODO.

    You can find the source code of the `Flopper` contract here:
    <https://github.com/makerdao/dss/blob/master/src/flop.sol>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Flopper` contract.
    """

    abi = Contract._load_abi(__name__, 'abi/Flopper.abi')
    bin = Contract._load_bin(__name__, 'abi/Flopper.bin')

    class Bid:
        def __init__(self, bid: Wad, lot: Wad, guy: Address, tic: int, end: int, vow: Address):
            assert(isinstance(bid, Wad))
            assert(isinstance(lot, Wad))
            assert(isinstance(guy, Address))
            assert(isinstance(tic, int))
            assert(isinstance(end, int))
            assert(isinstance(vow, Address))

            self.bid = bid
            self.lot = lot
            self.guy = guy
            self.tic = tic
            self.end = end
            self.vow = vow

    @staticmethod
    def deploy(web3: Web3, dai: Address, gem: Address):
        assert(isinstance(dai, Address))
        assert(isinstance(gem, Address))

        return Flopper(web3=web3, address=Contract._deploy(web3, Flopper.abi, Flopper.bin, [dai.address, gem.address]))

    def __init__(self, web3: Web3, address: Address):
        super(Flopper, self).__init__(web3, address, Flopper.abi, self.bids)

    def live(self) -> bool:
        return self._contract.call().live() > 0

    def approve(self, approval_function):
        """Approve the `Flapper` to access our `gem` so we can participate in auctions.

        For available approval functions (i.e. approval modes) see `directly` and `via_tx_manager`
        in `pymaker.approval`.

        Args:
            approval_function: Approval function (i.e. approval mode).
        """
        assert(callable(approval_function))

        approval_function(ERC20Token(web3=self.web3, address=self.dai()), self.address, 'Flopper')

    def dai(self) -> Address:
        """Returns the `dai` token.

        Returns:
            The address of the `dai` token.
        """
        return Address(self._contract.call().dai())

    def gem(self) -> Address:
        """Returns the `gem` token.

        Returns:
            The address of the `gem` token.
        """
        return Address(self._contract.call().gem())

    def bids(self, id: int) -> Bid:
        """Returns the auction details.

        Args:
            id: Auction identifier.

        Returns:
            The auction details.
        """
        assert(isinstance(id, int))

        array = self._contract.call().bids(id)

        return Flopper.Bid(bid=Wad(array[0]),
                           lot=Wad(array[1]),
                           guy=Address(array[2]),
                           tic=int(array[3]),
                           end=int(array[4]),
                           vow=Address(array[5]))

    def kick(self, gal: Address, lot: Wad, bid: Wad) -> Transact:
        assert(isinstance(gal, Address))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kick', [gal.address,
                                                                                          lot.value,
                                                                                          bid.value])

    def dent(self, id: int, lot: Wad, bid: Wad) -> Transact:
        assert(isinstance(id, int))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'dent', [id, lot.value, bid.value])

    def deal(self, id: int) -> Transact:
        assert(isinstance(id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'deal', [id])

    def __repr__(self):
        return f"Flopper('{self.address}')"
