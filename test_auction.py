from web3 import Web3
from web3 import HTTPProvider
import time
import json
import math

from contracts.Address import Address
from contracts.DSToken import DSToken
from contracts.AuctionManager import AuctionManager


def wait_for_receipt(transaction_hash):
    while True:
        receipt = web3.eth.getTransactionReceipt(transaction_hash)
        if receipt != None and receipt['blockNumber'] != None:
            return receipt
        time.sleep(0.5)


our_buyer = Address('0x0061f1dbAf1e1B2E412A75D3eD6B48c3D7412D35') # buyer1

web3 = Web3(HTTPProvider(endpoint_uri='http://localhost:8545'))
web3.eth.defaultAccount = our_buyer.address

token_sold = DSToken(web3=web3, address='0x383105dc3dab1646119335ae54afdfd9f2af4713')
token_paid_with = DSToken(web3=web3, address='0x408f224724a7680b6172bd37bf482c50e2be5d02')

auction_manager = AuctionManager(web3=web3, address='0xc40affcbb4457400a145c90322714aa7b702d319')

# hash = token_paid_with.approve(auction_manager.address, 1000*1000000000000000000)
# receipt = wait_for_receipt(hash)
# print(receipt)


print(token_paid_with.balance_of(our_buyer.address))
print(token_paid_with.allowance_of(our_buyer.address, auction_manager.address))
# exit(-1)

# time.sleep(1000)

max_buy_amount = 12300000000000000000
maximum_step = 1000 #ignored so far

auction_manager.on_bid(lambda bid_auction_id:
                       print("*** Bid on " + str(bid_auction_id)))

# time.sleep(1000)

auction_id = 3

while True:
    auction_info = auction_manager.get_auction_info(auction_id)
    auctionlet_info = auction_manager.get_auctionlet_info(auction_id) #TODO fails if auctionlet doesn't exist anymore

    print("")
    print("Auction status is:")
    print(auction_info)
    print(auctionlet_info)
    print("")

    if auctionlet_info.last_bidder == our_buyer:
        print("We are winning, not doing anything")
        time.sleep(5)
    else:
        print("We are not winning, we should bid")

        current_buy_amount = auctionlet_info.buy_amount
        next_possible_buy_amount = int(math.ceil(current_buy_amount * (100 + auction_info.min_increase) / 100))
        if next_possible_buy_amount > max_buy_amount:
            print("We cannot afford paying " + str(next_possible_buy_amount) + ", quitting")
            break

        print("Bidding " + str(next_possible_buy_amount))
        bid_result = auction_manager.bid(auction_id, next_possible_buy_amount)
        print("Bid result: " + str(bid_result))
        time.sleep(5)





# bid_result = auction_manager.bid(auction_id, 7.5*1000000000000000000)
# print(bid_result)


print(auction_manager.get_auction_info(auction_id))
print(auction_manager.get_auctionlet_info(auction_id))
