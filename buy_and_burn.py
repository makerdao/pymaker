from web3 import HTTPProvider
from web3 import Web3

from auctions.Auctioner import Auctioner
from auctions.strategy.BidUpToMaxRateStrategy import BidUpToMaxRateStrategy
from auctions.strategy.ForgetGoneAuctionletsStrategy import ForgetGoneAuctionletsStrategy
from auctions.strategy.IgnoreWinningAuctionletsStrategy import IgnoreWinningAuctionletsStrategy
from auctions.strategy.OnlyOurPairStrategy import OnlyOurPairStrategy
from auctions.strategy.HandleExpiredAuctionletsStrategy import HandleExpiredAuctionletsStrategy
from contracts.Address import Address
from contracts.DSToken import DSToken
from contracts.ERC20Token import ERC20Token
from contracts.auctions.AuctionManager import AuctionManager

######################
# simulated Buy&Burn #
######################

web3 = Web3(HTTPProvider(endpoint_uri='http://localhost:8545'))

# AuctionManager instance
auction_manager_address = Address('0xc40affcbb4457400a145c90322714aa7b702d319')
auction_manager = AuctionManager(web3=web3, address=auction_manager_address)

# the address we are trading from
trader_address = Address('0x0061f1dbAf1e1B2E412A75D3eD6B48c3D7412D35') # buyer1
web3.eth.defaultAccount = trader_address.address

# DAI is what is being sold
dai_address = Address('0x383105dc3dab1646119335ae54afdfd9f2af4713')
dai_token = ERC20Token(web3=web3, address=dai_address)

# MKR is what we pay with
mkr_address = Address('0x408f224724a7680b6172bd37bf482c50e2be5d02')
mkr_token = DSToken(web3=web3, address=mkr_address)

# maximum MKR/DAI rate we are willing to pay
max_mkr_to_dai_rate = 0.4500






strategy = ForgetGoneAuctionletsStrategy(
    OnlyOurPairStrategy(dai_token, mkr_token,
        HandleExpiredAuctionletsStrategy(
            IgnoreWinningAuctionletsStrategy(
                BidUpToMaxRateStrategy(max_mkr_to_dai_rate, 0.8)
            )
        )
    )
)



auctioner = Auctioner(auction_manager, trader_address)
auctioner.start(strategy)

