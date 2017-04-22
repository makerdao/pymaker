import time


# TODO the class name is not proper English
from auctions.strategy.StrategyContext import StrategyContext


class Auctioner:
    def __init__(self, auction_manager, trader_address):
        self.auction_manager = auction_manager
        self.trader_address = trader_address
        self.active_auctionlets = []


    def start(self, strategy):
        # for auction discovery
        average_block_time_in_seconds = 4
        number_of_blocks_per_minute = int(60/average_block_time_in_seconds)
        number_of_hours_to_look_back_for_active_auctionlets = 24
        number_of_historical_blocks_to_scan_for_active_auctionlets = number_of_blocks_per_minute*60*number_of_hours_to_look_back_for_active_auctionlets

        self.auction_manager.discover_recent_auctionlets(number_of_historical_blocks_to_scan_for_active_auctionlets,
                                                         lambda auctionlet_id: self.active_auctionlets.append(auctionlet_id))

        self.auction_manager.on_new_auction(lambda auctionlet_id:
                               self.active_auctionlets.append(auctionlet_id))

        self.auction_manager.on_bid(lambda bid_auction_id:
                       print("*** Bid on " + str(bid_auction_id)))

        while True:
            for auctionlet_id in self.active_auctionlets[:]:
                print("Processing auctionlet " + str(auctionlet_id))
                auctionlet = self.auction_manager.get_auctionlet(auctionlet_id)

                result = strategy.perform(auctionlet, StrategyContext(self.auction_manager.address, self.trader_address))
                print("    Result: " + result.description)
                if result.forget: self.active_auctionlets.remove(auctionlet_id)
            time.sleep(5)
