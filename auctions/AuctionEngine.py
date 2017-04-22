import time

from auctions.StrategyContext import StrategyContext


class AuctionEngine:
    def __init__(self, auction_manager, trader_address, strategy, number_of_recent_blocks=None, frequency=60):
        self.auction_manager = auction_manager
        self.trader_address = trader_address
        self.strategy = strategy
        self.frequency = frequency
        self.number_of_recent_blocks = number_of_recent_blocks
        self.active_auctionlets = []


    def start(self):
        self._bind_events()
        self._discover_recent_auctionlets()
        while True:
            for auctionlet_id in self.active_auctionlets[:]:
                self._process_auctionlet(auctionlet_id)
            time.sleep(self.frequency)

    def _discover_recent_auctionlets(self):
        if (self.number_of_recent_blocks is not None):
            print(f"Looking for auctionlets in {self.number_of_recent_blocks} recent blocks...")
            self.auction_manager.discover_recent_auctionlets(self.number_of_recent_blocks, self._on_recovered_auctionlet)

    def _bind_events(self):
        print("Monitoring for new auctionlets...")
        self.auction_manager.on_new_auction(self._on_new_auctionlet)
        self.auction_manager.on_bid(self._on_bid)

    def _on_recovered_auctionlet(self, auctionlet_id):
        print(f"Found old auctionlet #{auctionlet_id}")
        self.active_auctionlets.append(auctionlet_id)
        self._process_auctionlet(auctionlet_id)

    def _on_new_auctionlet(self, auctionlet_id):
        print(f"Discovered new auctionlet #{auctionlet_id}")
        self.active_auctionlets.append(auctionlet_id)
        self._process_auctionlet(auctionlet_id)

    def _on_bid(self, auctionlet_id):
        if (auctionlet_id not in self.active_auctionlets):
            print(f"Discovered new bid on a previously unknown auctionlet #{auctionlet_id}")
            self.active_auctionlets.append(auctionlet_id)
        else:
            print(f"Discovered new bid on an existing auctionlet #{auctionlet_id}")
        self._process_auctionlet(auctionlet_id)

    def _process_auctionlet(self, auctionlet_id):
        print("Processing auctionlet " + str(auctionlet_id))
        auctionlet = self.auction_manager.get_auctionlet(auctionlet_id)

        result = self.strategy.perform(auctionlet, StrategyContext(self.auction_manager.address, self.trader_address))
        print("    Result: " + result.description)
        if result.forget: self.active_auctionlets.remove(auctionlet_id)
