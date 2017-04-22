from auctions.AuctionEngine import AuctionEngine
from auctions.BidUpToMaxRateStrategy import BidUpToMaxRateStrategy
from auctions.HandleExpiredAuctionletsStrategy import HandleExpiredAuctionletsStrategy
from auctions.IgnoreWinningAuctionletsStrategy import IgnoreWinningAuctionletsStrategy
from auctions.OnlyOneTokenPairPairStrategy import OnlyOneTokenPairPairStrategy
from auctions.ForgetGoneAuctionletsStrategy import ForgetGoneAuctionletsStrategy
from contracts.Address import Address
from contracts.DSToken import DSToken
from contracts.ERC20Token import ERC20Token
from contracts.auctions.AuctionManager import AuctionManager

from web3 import HTTPProvider
from web3 import Web3


######################
# simulated Buy&Burn #
######################

web3 = Web3(HTTPProvider(endpoint_uri='http://localhost:8545'))

# AuctionManager instance
auction_manager_address = Address('0xc40affcbb4457400a145c90322714aa7b702d319')
auction_manager = AuctionManager(web3=web3, address=auction_manager_address)

# the address we are trading from
trader_address = Address('0x0061f1dbAf1e1B2E412A75D3eD6B48c3D7412D35') # buyer1

#TODO we should not rely on the default account
#TODO replace with 'from' everywhere
web3.eth.defaultAccount = trader_address.address

# DAI is what is being sold
dai_address = Address('0x383105dc3dab1646119335ae54afdfd9f2af4713')
dai_token = ERC20Token(web3=web3, address=dai_address)

# MKR is what we pay with
mkr_address = Address('0x408f224724a7680b6172bd37bf482c50e2be5d02')
mkr_token = DSToken(web3=web3, address=mkr_address)

# maximum MKR/DAI rate we are willing to pay
max_mkr_to_dai_rate = 0.4500
percentage_step = 0.8



# TODO fetch auctionlet data only once, not with each 'info' call



# for auction discovery
average_block_time_in_seconds = 4
number_of_blocks_per_minute = int(60/average_block_time_in_seconds)
number_of_hours_to_look_back_for_active_auctionlets = 24
number_of_historical_blocks_to_scan_for_active_auctionlets = number_of_blocks_per_minute*60*number_of_hours_to_look_back_for_active_auctionlets

strategy = BidUpToMaxRateStrategy(max_mkr_to_dai_rate, percentage_step)
strategy = IgnoreWinningAuctionletsStrategy(strategy)
strategy = HandleExpiredAuctionletsStrategy(strategy)
strategy = OnlyOneTokenPairPairStrategy(dai_token, mkr_token, strategy)
strategy = ForgetGoneAuctionletsStrategy(strategy)



engine = AuctionEngine(auction_manager, trader_address, strategy, 100000)
engine.start()

