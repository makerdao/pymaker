import time

from web3 import HTTPProvider
from web3 import Web3

from auctions.BasicProcessor import BasicProcessor
from auctions.DumbStrategy import DumbStrategy
from contracts.Address import Address
from contracts.DSToken import DSToken
from contracts.ERC20Token import ERC20Token
from contracts.auctions.AuctionManager import AuctionManager


def wait_for_receipt(transaction_hash):
    while True:
        receipt = web3.eth.getTransactionReceipt(transaction_hash)
        if receipt != None and receipt['blockNumber'] != None:
            return receipt
        time.sleep(0.5)


our_buyer = Address('0x0061f1dbAf1e1B2E412A75D3eD6B48c3D7412D35') # buyer1

web3 = Web3(HTTPProvider(endpoint_uri='http://localhost:8545'))
web3.eth.defaultAccount = our_buyer.address


# simulated Buy&Burn
# DAI is what is being sold
dai_address = Address('0x383105dc3dab1646119335ae54afdfd9f2af4713')
dai_token = ERC20Token(web3=web3, address=dai_address)

# MKR is what we pay with
mkr_address = Address('0x408f224724a7680b6172bd37bf482c50e2be5d02')
mkr_token = DSToken(web3=web3, address=mkr_address)

# maximum MKR/DAI rate we are willing to pay
max_mkr_to_dai_rate = 0.4500



# for auction discovery
average_block_time_in_seconds = 4
number_of_blocks_per_minute = int(60/average_block_time_in_seconds)
number_of_hours_to_look_back_for_active_auctionlets = 24
number_of_historical_blocks_to_scan_for_active_auctionlets = number_of_blocks_per_minute*60*number_of_hours_to_look_back_for_active_auctionlets

# print(number_of_historical_blocks_to_scan_for_active_auctionlets)


active_auctionlets = []

auction_manager_address = Address('0xc40affcbb4457400a145c90322714aa7b702d319')
auction_manager = AuctionManager(web3=web3, address=auction_manager_address)

auction_manager.discover_recent_auctionlets(number_of_historical_blocks_to_scan_for_active_auctionlets, lambda auctionlet_id: active_auctionlets.append(auctionlet_id))

# time.sleep(60)
# exit(-1)

strategy = DumbStrategy(dai_token, mkr_token, max_mkr_to_dai_rate, 0.8)
processor = BasicProcessor(strategy)

# hash = token_paid_with.approve(auction_manager.address, 1000*1000000000000000000)
# receipt = wait_for_receipt(hash)
# print(receipt)


# print(token_buy.balance_of(our_buyer.address))
# print(token_buy.allowance_of(our_buyer.address, auction_manager.address))
# exit(-1)

# time.sleep(1000)

# max_buy_amount = 12300000000000000000
# maximum_step = 1000 #ignored so far

auction_manager.on_bid(lambda bid_auction_id:
                       print("*** Bid on " + str(bid_auction_id)))

# time.sleep(1000)

# auction_id = 4




    # time.sleep(5)
    # if action is not None:
    # else:
    #     print("But the strategy said we cannot afford it")



# active_auctions = [4]

while True:
    for auctionlet_id in active_auctionlets[:]:
        print("Processing auctionlet " + str(auctionlet_id))
        auctionlet = auction_manager.get_auctionlet(auctionlet_id)
        result = processor.process_auctionlet(auctionlet, our_buyer, auction_manager.address)
        print("Result: " + result.description)
        if result.forget_auctionlet: active_auctionlets.remove(auctionlet_id)
    time.sleep(5)





# bid_result = auction_manager.bid(auction_id, 7.5*1000000000000000000)
# print(bid_result)


# print(auction_manager.__get_auction_info(auction_id))
# print(auction_manager.__get_auctionlet_info(auction_id))
