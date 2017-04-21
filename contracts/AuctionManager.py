import collections
import json
import time
from pprint import pformat

class AuctionManager:
    def __init__(self, web3, address):
        abi = self.__abi('contracts/AuctionManager.abi')
        self.web3 = web3
        self.address = address
        self.contract = web3.eth.contract(abi=abi)(address=address)
        self.state = {}

    def __abi(self, path):
        with open(path) as f:
            abi = json.load(f)
        return abi

    def reconstruct(self):
        """Scan over the event history and determine the current
        state of the auction (following splits).
        """

    def get_auction_info(self, auction_id):
        return AuctionInfo(self.contract.call().getAuctionInfo(auction_id))

    def get_auctionlet_info(self, auctionlet_id):
        return AuctionletInfo(self.contract.call().getAuctionletInfo(auctionlet_id))

    def bid(self, auction_id, how_much):
        """
        """
        # try:
        tx_hash = self.contract.transact().bid(auction_id, how_much)
        self.wait_for_receipt(tx_hash)
        return True
        # except:
        #
        #     return False

    def wait_for_receipt(self, transaction_hash):
        while True:
            receipt = self.web3.eth.getTransactionReceipt(transaction_hash)
            if receipt != None and receipt['blockNumber'] != None:
                return receipt
            time.sleep(0.5)


    # def bid(self, auction_id, how_much, quantity):
    #     """
    #     """


class AuctionInfo:
    def __init__(self, auction_info):
        self.creator = auction_info[0]
        self.buying = auction_info[1]
        self.selling = auction_info[2]
        self.start_bid = auction_info[3]
        self.min_increase = auction_info[4]
        self.min_decrease = auction_info[5]
        self.sell_amount = auction_info[6]
        self.ttl = auction_info[7]
        self.reversed = auction_info[8]
        self.unsold = auction_info[9]

    def __str__(self):
        return pformat (vars(self))


class AuctionletInfo:
    def __init__(self, auctionlet_info):
        self.auction_id = auctionlet_info[0]
        self.last_bidder = auctionlet_info[1]
        self.last_bid_time = auctionlet_info[2]
        self.buy_amount = auctionlet_info[3]
        self.sell_amount = auctionlet_info[4]
        self.unclaimed = auctionlet_info[5]
        self.base = auctionlet_info[6]

    def __str__(self):
        return pformat (vars(self))
