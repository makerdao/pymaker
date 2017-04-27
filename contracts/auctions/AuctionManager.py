from pprint import pformat
import datetime

from contracts.Address import Address
from contracts.Contract import Contract
from contracts.ERC20Token import ERC20Token
from contracts.Wad import Wad


class AuctionManager(Contract):
    """Nice wrapper around AuctionManager and SplittingAuctionManager

    Wrapper around AuctionManager and SplittingAuctionManager, Ethereum contracts that provide a set of auctions
    for use with standard tokens (https://github.com/makerdao/token-auction).

    There are two basic entities in this ecosystem:
    * Auctions.
    * Auctionlets - the splittable unit of an auction. Each auction initially has a single auctionlet.
      Auctionlets are the object on which bidders place bids. Splitting an auctionlet produces a new auctionlet
      of reduced quantity and reduces the available quantity in the original auctionlet.

    For now, only forward and non-splitting auctions are supported.
    """
    def __init__(self, web3, address):
        self.address = address
        self._contract = web3.eth.contract(abi=self._load_abi(__name__, 'AuctionManager.abi'))(address=address.address)
        self._web3 = web3
        self._our_tx_hashes = set()

        self._on_new_auction_handler = None
        self._on_bid_handler = None
        self._on_split_handler = None
        self._on_auction_reversal_handler = None

        self._contract.on('LogNewAuction', None, self._on_new_auction)
        self._contract.on('LogBid', None, self._on_bid)
        self._contract.on('LogSplit', None, self._on_split)
        self._contract.on('LogAuctionReversal', None, self._on_auction_reversal)




    def _on_new_auction(self, log):
        if log['transactionHash'] not in self._our_tx_hashes:
            if self._on_new_auction_handler is not None:
                self._on_new_auction_handler(log['args']['base_id'])

    def _on_bid(self, log):
        if log['transactionHash'] not in self._our_tx_hashes:
            if self._on_bid_handler is not None:
                self._on_bid_handler(log['args']['auctionlet_id'])

    def _on_split(self, log):
        if log['transactionHash'] not in self._our_tx_hashes:
            if self._on_split_handler is not None:
                self._on_split_handler(log['args']['base_id'], log['args']['new_id'], log['args']['split_id'])

    def _on_auction_reversal(self, log):
        if log['transactionHash'] not in self._our_tx_hashes:
            if self._on_auction_reversal_handler is not None:
                self._on_auction_reversal_handler(log['args']['auction_id'])

    def on_new_auction(self, handler):
        self._on_new_auction_handler = handler

    def on_bid(self, handler):
        self._on_bid_handler = handler

    def on_split(self, handler):
        self._on_split_handler = handler

    def on_auction_reversal(self, handler):
        self._on_auction_reversal_handler = handler

    def discover_recent_auctionlets(self, number_of_historical_blocks, on_auctionlet_discovered):
        """Scan over LogNewAuction event history and determine which auctions can still be active."""
        start_block_number = self._web3.eth.blockNumber - int(number_of_historical_blocks)
        return self._contract.pastEvents('LogNewAuction', {'fromBlock': start_block_number},
                                         lambda log: on_auctionlet_discovered(log['args']['base_id']))

    # def reconstruct(self):
    #     """Scan over the event history and determine the current
    #     state of the auction (following splits).
    #     """

    def get_auction(self, auction_id):
        """Returns an auction with specified identifier."""
        return Auction(self, auction_id, self._contract.call().getAuctionInfo(auction_id))

    def get_auctionlet(self, auctionlet_id):
        """Returns an auctionlet with specified identifier.

        In case of expired and claimed auctionlets, this methods returns 'None' as an indicator that
        the auctionlet isn't available anymore (the contract method basically throws in that case).
        """
        try:
            return Auctionlet(self, auctionlet_id, self._contract.call().getAuctionletInfo(auctionlet_id))
        except:
            return None

    def _is_auctionlet_expired(self, auctionlet_id):
        # in case of expired and claimed auctionlets, the contract method throws
        # so we return 'None' to let caller know the auctionlet isn't available anymore
        try:
            return self._contract.call().isExpired(auctionlet_id)
        except:
            return None

    def _bid(self, auctionlet_id, how_much):
        """
        """
        try:
            tx_hash = self._contract.transact().bid(auctionlet_id, int(how_much))
            self._our_tx_hashes.add(tx_hash)
            receipt = self._wait_for_receipt(tx_hash)
            receipt_logs = receipt['logs']
            return (receipt_logs is not None) and (len(receipt_logs) > 0)
        except:
            return False

    def _claim(self, auctionlet_id):
        """
        """
        try:
            tx_hash = self._contract.transact().claim(auctionlet_id)
            receipt = self._wait_for_receipt(tx_hash)
            receipt_logs = receipt['logs']
            return (receipt_logs is not None) and (len(receipt_logs) > 0)
        except:
            return False


class Auction:
    def __init__(self, auction_manager, auction_id, auction_info):
        self._auction_manager = auction_manager
        self.auction_id = auction_id
        self.creator = Address(auction_info[0])
        self.selling = ERC20Token(web3=auction_manager._web3, address=Address(auction_info[1]))
        self.buying = ERC20Token(web3=auction_manager._web3, address=Address(auction_info[2]))
        self.start_bid = Wad(auction_info[3])
        self.min_increase = auction_info[4]
        self.min_decrease = auction_info[5]
        self.sell_amount = Wad(auction_info[6])
        self.ttl = auction_info[7]
        self.reversed = auction_info[8]
        self.unsold = auction_info[9]

    def __eq__(self, other):
        return self.auction_id == other.auction_id

    def __str__(self):
        return pformat(vars(self))


class Auctionlet:
    def __init__(self, auction_manager, auctionlet_id, auctionlet_info):
        self._auction_manager = auction_manager
        self._auction = None
        self.auctionlet_id = auctionlet_id
        self.auction_id = auctionlet_info[0]
        self.last_bidder = Address(auctionlet_info[1])
        self.last_bid_time = datetime.datetime.fromtimestamp(auctionlet_info[2])
        self.buy_amount = Wad(auctionlet_info[3])
        self.sell_amount = Wad(auctionlet_info[4])
        self.unclaimed = auctionlet_info[5]
        self.base = auctionlet_info[6]

    def is_expired(self):
        return self._auction_manager._is_auctionlet_expired(self.auctionlet_id)

    def get_auction(self):
        if self._auction is None:
            self._auction = self._auction_manager.get_auction(self.auction_id)
        return self._auction

    def bid(self, how_much):
        return self._auction_manager._bid(self.auctionlet_id, how_much.value)

    def claim(self):
        return self._auction_manager._claim(self.auctionlet_id)

    def __eq__(self, other):
        return self.auctionlet_id == other.auctionlet_id

    def __str__(self):
        return pformat(vars(self))
