from web3 import Web3
from web3 import HTTPProvider
import time
import json

from contracts.DSToken import DSToken
from contracts.AuctionManager import AuctionManager


def wait_for_receipt(transaction_hash):
    while True:
        receipt = web3.eth.getTransactionReceipt(transaction_hash)
        if receipt != None and receipt['blockNumber'] != None:
            return receipt
        time.sleep(0.5)


web3 = Web3(HTTPProvider(endpoint_uri='http://localhost:8545'))
web3.eth.defaultAccount = '0x0061f1dbAf1e1B2E412A75D3eD6B48c3D7412D35' # buyer1

token_sold = DSToken(web3=web3, address='0x383105dc3dab1646119335ae54afdfd9f2af4713')
token_paid_with = DSToken(web3=web3, address='0x408f224724a7680b6172bd37bf482c50e2be5d02')

auction_manager = AuctionManager(web3=web3, address='0xc40affcbb4457400a145c90322714aa7b702d319')

# hash = token_paid_with.approve(auction_manager.address, 1000*1000000000000000000)
# receipt = wait_for_receipt(hash)
# print(receipt)


print(auction_manager.get_auction_info(2))
print(auction_manager.get_auctionlet_info(2))


bid_result = auction_manager.bid(2, int(7.5*1000000000000000000))
print(bid_result)


print(auction_manager.get_auction_info(2))
print(auction_manager.get_auctionlet_info(2))
