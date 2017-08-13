# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import threading
import time

import logging
from sortedcontainers import SortedSet

from keepers.auctions.StrategyContext import StrategyContext


class AuctionEngine:
    def __init__(self, auction_manager, trader_address, strategy, frequency):
        self.auction_manager = auction_manager
        self.trader_address = trader_address
        self.strategy = strategy
        self.frequency = frequency
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
        self.auction_manager.discover_recent_auctionlets(self._on_recovered_auctionlet)

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
        logging.info(f"{heading} [  selling: {str(auctionlet.sell_amount).rjust(25)} {auction.selling.name()}] [     creator: {auction.creator}]")
        logging.info(f"{padding} [ last_bid: {str(auctionlet.buy_amount).rjust(25)} {auction.buying.name()}] [ last_bidder: {auctionlet.last_bidder} (@ {auctionlet.last_bid_time})]" )
        logging.info(f"{padding} [    price: {price.rjust(21)} {auction.buying.name()}/{auction.selling.name()}] [  parameters: min_incr={auction.min_increase}, min_decr={auction.min_decrease}, ttl={auction.ttl}, reversed={auction.reversed}, expired={auctionlet.expired}]")

    def _print_auctionlet_outcome(self, auctionlet_id, result):
        padding = ' ' * len(self._heading(auctionlet_id))
        logging.info(f"{padding} [  outcome: {result}]")
        logging.info("")

    def _heading(self, auctionlet_id):
        return f"Auctionlet #{auctionlet_id}:"
