import time
import threading
from sortedcontainers import SortedSet

from auctions.StrategyContext import StrategyContext


class AuctionEngine:
    def __init__(self, auction_manager, trader_address, strategy, frequency, number_of_recent_blocks):
        self.auction_manager = auction_manager
        self.trader_address = trader_address
        self.strategy = strategy
        self.frequency = frequency
        self.number_of_recent_blocks = number_of_recent_blocks
        self._active_auctionlets = SortedSet()
        self._process_lock = threading.Lock()
        self._set_lock = threading.Lock()

    def start(self):
        self._bind_events()
        self._discover_recent_auctionlets()
        while True:
            for auctionlet_id in self._active_auctionlets[:]:
                self._process_auctionlet(auctionlet_id)
            time.sleep(self.frequency)

    def _bind_events(self):
        self.auction_manager.on_new_auction(self._on_new_auctionlet)
        self.auction_manager.on_bid(self._on_bid)
        self.auction_manager.on_split(self._on_split)

    def _discover_recent_auctionlets(self):
        if (self.number_of_recent_blocks is not None):
            self.auction_manager.discover_recent_auctionlets(self.number_of_recent_blocks, self._on_recovered_auctionlet)

    def _on_recovered_auctionlet(self, auctionlet_id):
        self._register_auctionlet(auctionlet_id)
        self._process_auctionlet(auctionlet_id)

    def _on_new_auctionlet(self, auctionlet_id):
        self._register_auctionlet(auctionlet_id)
        self._process_auctionlet(auctionlet_id)

    def _on_bid(self, auctionlet_id):
        self._register_auctionlet(auctionlet_id)
        self._process_auctionlet(auctionlet_id)

    def _on_split(self, base_id, new_id, split_id):
        self._register_auctionlet(new_id)
        self._register_auctionlet(split_id)
        self._process_auctionlet(new_id)
        self._process_auctionlet(split_id)

    def _register_auctionlet(self, auctionlet_id):
        with self._set_lock:
            self._active_auctionlets.add(auctionlet_id)

    def _unregister_auctionlet(self, auctionlet_id):
        with self._set_lock:
            try:
                self._active_auctionlets.remove(auctionlet_id)
            except:
                pass

    def _process_auctionlet(self, auctionlet_id):
        with self._process_lock:
            auctionlet = self.auction_manager.get_auctionlet(auctionlet_id)
            if auctionlet is not None:
                self._print_auctionlet(auctionlet_id, auctionlet)
                result = self.strategy.perform(auctionlet, StrategyContext(self.auction_manager.address, self.trader_address))
                self._print_auctionlet_outcome(auctionlet_id, result.description)
                if result.forget:
                    self._unregister_auctionlet(auctionlet_id)
            else:
                self._unregister_auctionlet(auctionlet_id)

    def _print_auctionlet(self, auctionlet_id, auctionlet):
        auction = auctionlet.get_auction()
        heading = self._heading(auctionlet_id)
        padding = ' ' * len(heading)
        price = "{0:.8f}".format(auctionlet.sell_amount / auctionlet.buy_amount)
        print(f"{heading} [  selling: {str(auctionlet.sell_amount).rjust(25)} {auction.selling.name()}] [     creator: {auction.creator}]")
        print(f"{padding} [ last_bid: {str(auctionlet.buy_amount).rjust(25)} {auction.buying.name()}] [ last_bidder: {auctionlet.last_bidder} (@ {auctionlet.last_bid_time})]" )
        print(f"{padding} [    price: {price.rjust(21)} {auction.buying.name()}/{auction.selling.name()}] [  parameters: min_incr={auction.min_increase}, min_decr={auction.min_decrease}, ttl={auction.ttl}, reversed={auction.reversed}, expired={auctionlet.expired}]")

    def _print_auctionlet_outcome(self, auctionlet_id, result):
        padding = ' ' * len(self._heading(auctionlet_id))
        print(f"{padding} [  outcome: {result}]")
        print("")

    def _heading(self, auctionlet_id):
        return f"Auctionlet #{auctionlet_id}:"
