# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2018 reverendus, bargst
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
from pymaker.numeric import Ray
from web3 import Web3

from pymaker import Contract, Address, Transact, Wad
from pymaker.token import ERC20Token


class Flipper(Contract):
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
        def __init__(self, bid: Wad, lot: Wad, guy: Address, tic: int, end: int, urn: Address, gal: Address, tab: Wad):
            assert(isinstance(bid, Wad))
            assert(isinstance(lot, Wad))
            assert(isinstance(guy, Address))
            assert(isinstance(tic, int))
            assert(isinstance(end, int))
            assert(isinstance(urn, Address))
            assert(isinstance(gal, Address))
            assert(isinstance(tab, Wad))

            self.bid = bid
            self.lot = lot
            self.guy = guy
            self.tic = tic
            self.end = end
            self.lad = urn
            self.gal = gal
            self.tab = tab

    @staticmethod
    def deploy(web3: Web3, dai: Address, gem: Address):
        assert(isinstance(dai, Address))
        assert(isinstance(gem, Address))

        return Flipper(web3=web3, address=Contract._deploy(web3, Flipper.abi, Flipper.bin, [dai.address, gem.address]))

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def approve(self, approval_function):
        """Approve the `Flipper` to access our `dai` so we can participate in auctions.

        For available approval functions (i.e. approval modes) see `directly` and `via_tx_manager`
        in `pymaker.approval`. #TODO hope_directly()

        Args:
            approval_function: Approval function (i.e. approval mode).
        """
        assert(callable(approval_function))

        approval_function(ERC20Token(web3=self.web3, address=self.vat()), self.address, 'Flipper')

    def vat(self) -> Address:
        """Returns the `vat` token.
         Returns:
            The address of the `vat` token.
        """
        return Address(self._contract.call().vat())

    def gem(self) -> Address:
        """Returns the `gem` token.

        Returns:
            The address of the `gem` token.
        """
        return Address(self._contract.call().gem())

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

    def bids(self, id: int) -> Bid:
        """Returns the auction details.

        Args:
            id: Auction identifier.

        Returns:
            The auction details.
        """
        assert(isinstance(id, int))

        array = self._contract.call().bids(id)

        return Flipper.Bid(bid=Wad(array[0]),
                           lot=Wad(array[1]),
                           guy=Address(array[2]),
                           tic=int(array[3]),
                           end=int(array[4]),
                           urn=Address(Web3.toHex(array[5])[-40:]),
                           gal=Address(array[6]),
                           tab=Wad(array[7]))

    def kick(self, urn: Address, gal: Address, tab: Wad, lot: Wad, bid: Wad) -> Transact:
        assert(isinstance(urn, Address))
        assert(isinstance(gal, Address))
        assert(isinstance(tab, Wad))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Wad))

        bytes32_urn = Web3.toBytes(hexstr='0x'+urn.address[2:].zfill(64))
        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kick', [bytes32_urn,
                                                                                          gal.address,
                                                                                          tab.value,
                                                                                          lot.value,
                                                                                          bid.value])

    def tend(self, id: int, lot: Wad, bid: Wad) -> Transact:
        assert(isinstance(id, int))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'tend', [id, lot.value, bid.value])

    def dent(self, id: int, lot: Wad, bid: Wad) -> Transact:
        assert(isinstance(id, int))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'dent', [id, lot.value, bid.value])

    def deal(self, id: int) -> Transact:
        assert(isinstance(id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'deal', [id])

    def __repr__(self):
        return f"Flipper('{self.address}')"


class Flapper(Contract):
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
        def __init__(self, bid: Wad, lot: Wad, guy: Address, tic: int, end: int, gal: Address):
            assert(isinstance(bid, Wad))
            assert(isinstance(lot, Wad))
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

    @staticmethod
    def deploy(web3: Web3, dai: Address, gem: Address):
        assert(isinstance(dai, Address))
        assert(isinstance(gem, Address))

        return Flapper(web3=web3, address=Contract._deploy(web3, Flapper.abi, Flapper.bin, [dai.address, gem.address]))

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def approve(self, approval_function):
        """Approve the `Flapper` to access our `gem` so we can participate in auctions.

        For available approval functions (i.e. approval modes) see `directly` and `via_tx_manager`
        in `pymaker.approval`.

        Args:
            approval_function: Approval function (i.e. approval mode).
        """
        assert(callable(approval_function))

        approval_function(ERC20Token(web3=self.web3, address=self.gem()), self.address, 'Flapper')

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
                           lot=Wad(array[1]),
                           guy=Address(array[2]),
                           tic=int(array[3]),
                           end=int(array[4]),
                           gal=Address(array[5]))

    def kick(self, gal: Address, lot: Wad, bid: Wad) -> Transact:
        assert(isinstance(gal, Address))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kick', [gal.address,
                                                                                          lot.value,
                                                                                          bid.value])

    def tend(self, id: int, lot: Wad, bid: Wad) -> Transact:
        assert(isinstance(id, int))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'tend', [id, lot.value, bid.value])

    def deal(self, id: int) -> Transact:
        assert(isinstance(id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'deal', [id])

    def __repr__(self):
        return f"Flapper('{self.address}')"


class Flopper(Contract):
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
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self._contract = self._get_contract(web3, self.abi, address)

    def rely(self, guy: Address) -> Transact:
        assert isinstance(guy, Address)

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'rely', [guy.address])

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
