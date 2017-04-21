import collections
import json
import time
from pprint import pformat

from contracts.Address import Address


class AuctionManager:
    def __init__(self, web3, address):
        abi = self.__abi('contracts/AuctionManager.abi')
        self.web3 = web3
        self.address = address
        self.contract = web3.eth.contract(abi=abi)(address=address)
        self.__our_tx_hashes = set()

        self.__on_new_auction_handler = None
        self.contract.on('LogNewAuction', None, self.__on_new_auction)
        self.__on_bid_handler = None
        self.contract.on('LogBid', None, self.__on_bid)
        self.__on_split_handler = None
        self.contract.on('LogSplit', None, self.__on_split)
        self.__on_auction_reversal_handler = None
        self.contract.on('LogAuctionReversal', None, self.__on_auction_reversal)




    def __abi(self, path):
        with open(path) as f:
            abi = json.load(f)
        return abi

    def __on_new_auction(self, log):
        if log['transactionHash'] not in self.__our_tx_hashes:
            if self.__on_new_auction_handler is not None:
                self.__on_new_auction_handler(log['args']['base_id'])

    def __on_bid(self, log):
        if log['transactionHash'] not in self.__our_tx_hashes:
            if self.__on_bid_handler is not None:
                self.__on_bid_handler(log['args']['auctionlet_id'])

    def __on_split(self, log):
        if log['transactionHash'] not in self.__our_tx_hashes:
            if self.__on_split_handler is not None:
                self.__on_split_handler(log['args']['base_id'], log['args']['new_id'], log['args']['split_id'])

    def __on_auction_reversal(self, log):
        if log['transactionHash'] not in self.__our_tx_hashes:
            if self.__on_auction_reversal_handler is not None:
                self.__on_auction_reversal_handler(log['args']['auction_id'])

    def on_new_auction(self, handler):
        self.__on_new_auction_handler = handler

    def on_bid(self, handler):
        self.__on_bid_handler = handler

    def on_split(self, handler):
        self.__on_split_handler = handler

    def on_auction_reversal(self, handler):
        self.__on_auction_reversal_handler = handler

    # def reconstruct(self):
    #     """Scan over the event history and determine the current
    #     state of the auction (following splits).
    #     """

    def get_auction(self, auction_id):
        return Auction(self, auction_id)

    def get_auction_info(self, auction_id):
        return AuctionInfo(self.contract.call().getAuctionInfo(auction_id))

    def get_auctionlet(self, auctionlet_id):
        return Auctionlet(self, auctionlet_id)

    def get_auctionlet_info(self, auctionlet_id):
        # in case of expired and claimed auctionlets, the contract method throws
        # so we return 'None' to let caller know the auctionlet isn't available anymore
        try:
            return AuctionletInfo(self.contract.call().getAuctionletInfo(auctionlet_id))
        except:
            return None

    def is_auctionlet_expired(self, auctionlet_id):
        # in case of expired and claimed auctionlets, the contract method throws
        # so we return 'None' to let caller know the auctionlet isn't available anymore
        try:
            return self.contract.call().isExpired(auctionlet_id)
        except:
            return None

    def bid(self, auction_id, how_much):
        """
        """
        try:
            tx_hash = self.contract.transact().bid(auction_id, int(how_much))
            self.__our_tx_hashes.add(tx_hash)
            receipt = self.wait_for_receipt(tx_hash)
            receipt_logs = receipt['logs']
            return (receipt_logs is not None) and (len(receipt_logs) > 0)
        except:
            return False

    def wait_for_receipt(self, transaction_hash):
        while True:
            receipt = self.web3.eth.getTransactionReceipt(transaction_hash)
            if receipt != None and receipt['blockNumber'] != None:
                return receipt
            time.sleep(0.5)


    # def bid(self, auction_id, how_much, quantity):
    #     """
    #     """


class Auction:
    def __init__(self, auction_manager, auction_id):
        self.auction_manager = auction_manager
        self.auction_id = auction_id

    def get_info(self):
        return self.auction_manager.get_auction_info(self.auction_id)

    def __str__(self):
        return f"Auction(auction_id={self.auction_id})"


class AuctionInfo:
    def __init__(self, auction_info):
        self.creator = Address(auction_info[0])
        self.selling = Address(auction_info[1])
        self.buying = Address(auction_info[2])
        self.start_bid = auction_info[3]
        self.min_increase = auction_info[4]
        self.min_decrease = auction_info[5]
        self.sell_amount = auction_info[6]
        self.ttl = auction_info[7]
        self.reversed = auction_info[8]
        self.unsold = auction_info[9]

    def __str__(self):
        return pformat (vars(self))


class Auctionlet:
    def __init__(self, auction_manager, auctionlet_id):
        self.auction_manager = auction_manager
        self.auctionlet_id = auctionlet_id

    def is_expired(self):
        return self.auction_manager.is_auctionlet_expired(self.auctionlet_id)

    def get_info(self):
        return self.auction_manager.get_auctionlet_info(self.auctionlet_id)

    def __str__(self):
        return f"Auctionlet(auctionlet_id={self.auctionlet_id})"


class AuctionletInfo:
    def __init__(self, auctionlet_info):
        self.auction_id = auctionlet_info[0]
        self.last_bidder = Address(auctionlet_info[1])
        self.last_bid_time = auctionlet_info[2]
        self.buy_amount = auctionlet_info[3]
        self.sell_amount = auctionlet_info[4]
        self.unclaimed = auctionlet_info[5]
        self.base = auctionlet_info[6]

    def __str__(self):
        return pformat (vars(self))

