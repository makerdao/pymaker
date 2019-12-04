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
from typing import List
from web3 import Web3
from web3.utils.events import get_event_data

from pymaker import Contract, Address, Transact
from pymaker.logging import LogNote
from pymaker.numeric import Wad, Rad, Ray
from pymaker.token import ERC20Token


def toBytes(string: str):
    assert(isinstance(string, str))
    return string.encode('utf-8').ljust(32, bytes(1))


class AuctionContract(Contract):
    """Abstract baseclass shared across all three auction contracts."""

    class DealLog:
        def __init__(self, lognote: LogNote):
            # This is whoever called `deal`, which could differ from the `guy` who won the auction
            self.usr = Address(lognote.usr)
            self.id = Web3.toInt(lognote.arg1)
            self.block = lognote.block
            self.tx_hash = lognote.tx_hash

        def __repr__(self):
            return f"AuctionContract.DealLog({pformat(vars(self))})"

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

        self.log_note_abi = None
        self.kick_abi = None
        for member in abi:
            if not self.log_note_abi and member.get('name') == 'LogNote':
                self.log_note_abi = member
            elif not self.kick_abi and member.get('name') == 'Kick':
                self.kick_abi = member

    def wards(self, address: Address) -> bool:
        assert isinstance(address, Address)

        return bool(self._contract.call().wards(address.address))

    def vat(self) -> Address:
        """Returns the `vat` address.
         Returns:
            The address of the `vat` contract.
        """
        return Address(self._contract.call().vat())

    def approve(self, source: Address, approval_function, **kwargs):
        """Approve the auction to access our collateral, Dai, or MKR so we can participate in auctions.

        For available approval functions (i.e. approval modes) see `directly` and `hope_directly`
        in `pymaker.approval`.

        Args:
            source: Address of the contract or token relevant to the auction (for Flipper and Flopper pass Vat address,
            for Flapper pass MKR token address)
            approval_function: Approval function (i.e. approval mode)
        """
        assert isinstance(source, Address)
        assert(callable(approval_function))

        approval_function(token=ERC20Token(web3=self.web3, address=source),
                          spender_address=self.address, spender_name=self.__class__.__name__, **kwargs)

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

    def beg(self) -> Wad:
        """Returns the percentage minimum bid increase.

        Returns:
            The percentage minimum bid increase.
        """
        return Wad(self._contract.call().beg())

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

    def deal(self, id: int) -> Transact:
        assert(isinstance(id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'deal', [id])

    def get_past_lognotes(self, number_of_past_blocks: int, abi: list) -> List[LogNote]:
        assert isinstance(number_of_past_blocks, int)
        assert isinstance(abi, list)

        block_number = self._contract.web3.eth.blockNumber
        filter_params = {
            'address': self.address.address,
            'fromBlock': max(block_number - number_of_past_blocks, 0),
            'toBlock': block_number
        }

        logs = self.web3.eth.getLogs(filter_params)
        events = list(map(lambda l: self.parse_event(l), logs))
        return list(filter(lambda l: l is not None, events))

    def parse_event(self, event):
        raise NotImplemented()


class Flipper(AuctionContract):
    """A client for the `Flipper` contract, used to interact with collateral auctions.

    You can find the source code of the `Flipper` contract here:
    <https://github.com/makerdao/dss/blob/master/src/flip.sol>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Flipper` contract.

    Event signatures:
        0x65fae35e: (deployment-related)
        0x9c52a7f1: (deployment-related)
        0x29ae8114: file
        0xc84ce3a1172f0dec3173f04caaa6005151a4bfe40d4c9f3ea28dba5f719b2a7a: kick
        0x4b43ed12: tend
        0x5ff3a382: dent
        0xc959c42b: deal
    """

    abi = Contract._load_abi(__name__, 'abi/Flipper.abi')
    bin = Contract._load_bin(__name__, 'abi/Flipper.bin')

    class Bid:
        def __init__(self, id: int, bid: Rad, lot: Wad, guy: Address, tic: int, end: int,
                     usr: Address, gal: Address, tab: Rad):
            assert(isinstance(id, int))
            assert(isinstance(bid, Rad))
            assert(isinstance(lot, Wad))
            assert(isinstance(guy, Address))
            assert(isinstance(tic, int))
            assert(isinstance(end, int))
            assert(isinstance(usr, Address))
            assert(isinstance(gal, Address))
            assert(isinstance(tab, Rad))

            self.id = id
            self.bid = bid
            self.lot = lot
            self.guy = guy
            self.tic = tic
            self.end = end
            self.usr = usr
            self.gal = gal
            self.tab = tab

        def __repr__(self):
            return f"Flipper.Bid({pformat(vars(self))})"

    class KickLog:
        def __init__(self, log):
            args = log['args']
            self.id = args['id']
            self.lot = Wad(args['lot'])
            self.bid = Rad(args['bid'])
            self.tab = Rad(args['tab'])
            self.usr = Address(args['usr'])
            self.gal = Address(args['gal'])
            self.block = log['blockNumber']
            self.tx_hash = log['transactionHash'].hex()

        def __repr__(self):
            return f"Flipper.KickLog({pformat(vars(self))})"

    class TendLog:
        def __init__(self, lognote: LogNote):
            self.guy = Address(lognote.usr)
            self.id = Web3.toInt(lognote.arg1)
            self.lot = Wad(Web3.toInt(lognote.arg2))
            self.bid = Rad(Web3.toInt(lognote.get_bytes_at_index(2)))
            self.block = lognote.block
            self.tx_hash = lognote.tx_hash

        def __repr__(self):
            return f"Flipper.TendLog({pformat(vars(self))})"

    class DentLog:
        def __init__(self, lognote: LogNote):
            self.guy = Address(lognote.usr)
            self.id = Web3.toInt(lognote.arg1)
            self.lot = Wad(Web3.toInt(lognote.arg2))
            self.bid = Rad(Web3.toInt(lognote.get_bytes_at_index(2)))
            self.block = lognote.block
            self.tx_hash = lognote.tx_hash

        def __repr__(self):
            return f"Flipper.DentLog({pformat(vars(self))})"

    def __init__(self, web3: Web3, address: Address):
        super(Flipper, self).__init__(web3, address, Flipper.abi, self.bids)

    def bids(self, id: int) -> Bid:
        """Returns the auction details.

        Args:
            id: Auction identifier.

        Returns:
            The auction details.
        """
        assert(isinstance(id, int))

        array = self._contract.call().bids(id)

        return Flipper.Bid(id=id,
                           bid=Rad(array[0]),
                           lot=Wad(array[1]),
                           guy=Address(array[2]),
                           tic=int(array[3]),
                           end=int(array[4]),
                           usr=Address(array[5]),
                           gal=Address(array[6]),
                           tab=Rad(array[7]))

    def kick(self, usr: Address, gal: Address, tab: Rad, lot: Wad, bid: Rad) -> Transact:
        assert(isinstance(usr, Address))
        assert(isinstance(gal, Address))
        assert(isinstance(tab, Rad))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Rad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kick', [usr.address,
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

    def past_logs(self, number_of_past_blocks: int):
        assert isinstance(number_of_past_blocks, int)
        logs = super().get_past_lognotes(number_of_past_blocks, Flipper.abi)

        history = []
        for log in logs:
            if log is None:
                continue
            elif isinstance(log, Flipper.KickLog):
                history.append(log)
            elif log.sig == '0x4b43ed12':
                history.append(Flipper.TendLog(log))
            elif log.sig == '0x5ff3a382':
                history.append(Flipper.DentLog(log))
            elif log.sig == '0xc959c42b':
                history.append(AuctionContract.DealLog(log))
        return history

    def parse_event(self, event):
        signature = Web3.toHex(event['topics'][0])
        if signature == "0xc84ce3a1172f0dec3173f04caaa6005151a4bfe40d4c9f3ea28dba5f719b2a7a":
            event_data = get_event_data(self.kick_abi, event)
            return Flipper.KickLog(event_data)
        else:
            event_data = get_event_data(self.log_note_abi, event)
            return LogNote(event_data)

    def __repr__(self):
        return f"Flipper('{self.address}')"


class Flapper(AuctionContract):
    """A client for the `Flapper` contract, used to interact with surplus auctions.

    You can find the source code of the `Flapper` contract here:
    <https://github.com/makerdao/dss/blob/master/src/flap.sol>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Flapper` contract.

    Event signatures:
        0x65fae35e: (deployment-related)
        0x9c52a7f1: (deployment-related)
        0xe6dde59cbc017becba89714a037778d234a84ce7f0a137487142a007e580d609: kick
        0x29ae8114: file
        0x4b43ed12: tend
        0xc959c42b: deal
    """

    abi = Contract._load_abi(__name__, 'abi/Flapper.abi')
    bin = Contract._load_bin(__name__, 'abi/Flapper.bin')

    class Bid:
        def __init__(self, id: int, bid: Wad, lot: Rad, guy: Address, tic: int, end: int):
            assert(isinstance(id, int))
            assert(isinstance(bid, Wad))        # MKR
            assert(isinstance(lot, Rad))        # DAI
            assert(isinstance(guy, Address))
            assert(isinstance(tic, int))
            assert(isinstance(end, int))

            self.id = id
            self.bid = bid
            self.lot = lot
            self.guy = guy
            self.tic = tic
            self.end = end

        def __repr__(self):
            return f"Flapper.Bid({pformat(vars(self))})"

    class KickLog:
        def __init__(self, log):
            args = log['args']
            self.id = args['id']
            self.lot = Rad(args['lot'])
            self.bid = Wad(args['bid'])
            self.block = log['blockNumber']
            self.tx_hash = log['transactionHash'].hex()

        def __repr__(self):
            return f"Flapper.KickLog({pformat(vars(self))})"

    class TendLog:
        def __init__(self, lognote: LogNote):
            self.guy = Address(lognote.usr)
            self.id = Web3.toInt(lognote.arg1)
            self.lot = Rad(Web3.toInt(lognote.arg2))
            self.bid = Wad(Web3.toInt(lognote.get_bytes_at_index(2)))
            self.block = lognote.block
            self.tx_hash = lognote.tx_hash

        def __repr__(self):
            return f"Flapper.TendLog({pformat(vars(self))})"

    def __init__(self, web3: Web3, address: Address):
        super(Flapper, self).__init__(web3, address, Flapper.abi, self.bids)

    def live(self) -> bool:
        return self._contract.call().live() > 0

    def bids(self, id: int) -> Bid:
        """Returns the auction details.

        Args:
            id: Auction identifier.

        Returns:
            The auction details.
        """
        assert(isinstance(id, int))

        array = self._contract.call().bids(id)

        return Flapper.Bid(id=id,
                           bid=Wad(array[0]),
                           lot=Rad(array[1]),
                           guy=Address(array[2]),
                           tic=int(array[3]),
                           end=int(array[4]))

    def kick(self, lot: Rad, bid: Wad) -> Transact:
        assert(isinstance(lot, Rad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kick', [lot.value,
                                                                                          bid.value])

    def tend(self, id: int, lot: Rad, bid: Wad) -> Transact:
        assert(isinstance(id, int))
        assert(isinstance(lot, Rad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'tend', [id, lot.value, bid.value])

    def tick(self, id: int) -> Transact:
        """Resurrect an auction which expired without any bids."""
        assert (isinstance(id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'tick', [id])

    def yank(self, id: int) -> Transact:
        """While `cage`d, refund current bid to the bidder"""
        assert (isinstance(id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'yank', [id])

    def past_logs(self, number_of_past_blocks: int):
        assert isinstance(number_of_past_blocks, int)
        logs = super().get_past_lognotes(number_of_past_blocks, Flapper.abi)

        history = []
        for log in logs:
            if log is None:
                continue
            elif isinstance(log, Flapper.KickLog):
                history.append(log)
            elif log.sig == '0x4b43ed12':
                history.append(Flapper.TendLog(log))
            elif log.sig == '0xc959c42b':
                history.append(AuctionContract.DealLog(log))
        return history

    def parse_event(self, event):
        signature = Web3.toHex(event['topics'][0])
        if signature == "0xe6dde59cbc017becba89714a037778d234a84ce7f0a137487142a007e580d609":
            event_data = get_event_data(self.kick_abi, event)
            return Flapper.KickLog(event_data)
        else:
            event_data = get_event_data(self.log_note_abi, event)
            return LogNote(event_data)

    def __repr__(self):
        return f"Flapper('{self.address}')"


class Flopper(AuctionContract):
    """A client for the `Flopper` contract, used to interact with debt auctions.

    You can find the source code of the `Flopper` contract here:
    <https://github.com/makerdao/dss/blob/master/src/flop.sol>.

    Attributes:
        web3: An instance of `Web` from `web3.py`.
        address: Ethereum address of the `Flopper` contract.

    Event signatures:
        0x65fae35e: (deployment-related)
        0x9c52a7f1: (deployment-related)
        0x29ae8114: file
        0x7e8881001566f9f89aedb9c5dc3d856a2b81e5235a8196413ed484be91cc0df6: kick
        0x5ff3a382: dent
        0xc959c42b: deal
    """

    abi = Contract._load_abi(__name__, 'abi/Flopper.abi')
    bin = Contract._load_bin(__name__, 'abi/Flopper.bin')

    class Bid:
        def __init__(self, id: int, bid: Rad, lot: Wad, guy: Address, tic: int, end: int):
            assert(isinstance(id, int))
            assert(isinstance(bid, Rad))
            assert(isinstance(lot, Wad))
            assert(isinstance(guy, Address))
            assert(isinstance(tic, int))
            assert(isinstance(end, int))

            self.id = id
            self.bid = bid
            self.lot = lot
            self.guy = guy
            self.tic = tic
            self.end = end

        def __repr__(self):
            return f"Flopper.Bid({pformat(vars(self))})"

    class KickLog:
        def __init__(self, log):
            args = log['args']
            self.id = args['id']
            self.lot = Wad(args['lot'])
            self.bid = Rad(args['bid'])
            self.gal = Address(args['gal'])
            self.block = log['blockNumber']
            self.tx_hash = log['transactionHash'].hex()

        def __repr__(self):
            return f"Flopper.KickLog({pformat(vars(self))})"

    class DentLog:
        def __init__(self, lognote: LogNote):
            self.guy = Address(lognote.usr)
            self.id = Web3.toInt(lognote.arg1)
            self.lot = Wad(Web3.toInt(lognote.arg2))
            self.bid = Rad(Web3.toInt(lognote.get_bytes_at_index(2)))
            self.block = lognote.block
            self.tx_hash = lognote.tx_hash

        def __repr__(self):
            return f"Flopper.DentLog({pformat(vars(self))})"

    def __init__(self, web3: Web3, address: Address):
        assert isinstance(web3, Web3)
        assert isinstance(address, Address)

        super(Flopper, self).__init__(web3, address, Flopper.abi, self.bids)

    def live(self) -> bool:
        return self._contract.call().live() > 0

    def pad(self) -> Wad:
        """Returns the lot increase applied after an auction has been `tick`ed."""

        return Wad(self._contract.call().pad())

    def bids(self, id: int) -> Bid:
        """Returns the auction details.

        Args:
            id: Auction identifier.

        Returns:
            The auction details.
        """
        assert(isinstance(id, int))

        array = self._contract.call().bids(id)

        return Flopper.Bid(id=id,
                           bid=Rad(array[0]),
                           lot=Wad(array[1]),
                           guy=Address(array[2]),
                           tic=int(array[3]),
                           end=int(array[4]))

    def kick(self, gal: Address, lot: Wad, bid: Wad) -> Transact:
        assert(isinstance(gal, Address))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Wad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'kick', [gal.address,
                                                                                          lot.value,
                                                                                          bid.value])

    def dent(self, id: int, lot: Wad, bid: Rad) -> Transact:
        assert(isinstance(id, int))
        assert(isinstance(lot, Wad))
        assert(isinstance(bid, Rad))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'dent', [id, lot.value, bid.value])

    def tick(self, id: int) -> Transact:
        """Resurrect an auction which expired without any bids."""
        assert (isinstance(id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'tick', [id])

    def yank(self, id: int) -> Transact:
        """While `cage`d, refund current bid to the bidder"""
        assert (isinstance(id, int))

        return Transact(self, self.web3, self.abi, self.address, self._contract, 'yank', [id])

    def past_logs(self, number_of_past_blocks: int):
        assert isinstance(number_of_past_blocks, int)
        logs = super().get_past_lognotes(number_of_past_blocks, Flopper.abi)

        history = []
        for log in logs:
            if log is None:
                continue
            elif isinstance(log, Flopper.KickLog):
                history.append(log)
            elif log.sig == '0x5ff3a382':
                history.append(Flopper.DentLog(log))
            elif log.sig == '0xc959c42b':
                history.append(AuctionContract.DealLog(log))
        return history

    def parse_event(self, event):
        signature = Web3.toHex(event['topics'][0])
        if signature == "0x7e8881001566f9f89aedb9c5dc3d856a2b81e5235a8196413ed484be91cc0df6":
            event_data = get_event_data(self.kick_abi, event)
            return Flopper.KickLog(event_data)
        else:
            event_data = get_event_data(self.log_note_abi, event)
            return LogNote(event_data)

    def __repr__(self):
        return f"Flopper('{self.address}')"
