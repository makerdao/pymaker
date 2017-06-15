#!/usr/bin/env python3
#
# This file is part of "maker.py".
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

import argparse
import datetime
import time

from web3 import HTTPProvider
from web3 import Web3

from contracts.Address import Address
from contracts.Ray import Ray
from contracts.Wad import Wad
from contracts.otc.SimpleMarket import SimpleMarket
from contracts.sai.Tub import Tub
from contracts.token.ERC20Token import ERC20Token
from contracts.value.DSValue import DSValue
from keepers.Config import Config
from keepers.Keeper import Keeper


class SaiProcessWoe(Keeper):
    def all_offers(self, market):
        all_offers = [market.get_offer(offer_id) for offer_id in range(1, market.get_last_offer_id()+1)]
        return [offer for offer in all_offers if offer is not None]

    def filter_by_token_pair(self, offers, sell_which_token, buy_which_token):
        return [offer for offer in offers if offer.sell_which_token == sell_which_token and offer.buy_which_token == buy_which_token]

    def sell_to_buy_price(self, offer):
        #TODO I think this is the reason of the rounding error
        return Ray.from_number(offer.sell_how_much/offer.buy_how_much)

    def buy_to_sell_price(self, offer):
        return Ray.from_number(offer.sell_how_much/offer.buy_how_much)

    def first_offer(self, offers):
        if len(offers) > 0: return offers[0]
        return None

    def setup_allowances(self):
        self.setup_allowance(self.skr, self.market.address)
        self.setup_allowance(self.sai, self.tub.address)

    def setup_allowance(self, token, address):
        minimum_allowance = Wad.from_number(1000000000)
        target_allowance = Wad.from_number(1000000000000)
        if token.allowance_of(self.our_address, address) < minimum_allowance:
            print(f"Raising {token.name()} allowance for {address}")
            token.approve(address, target_allowance)

    def process(self):
        print(f"")
        self.setup_allowances()
        print(f"Processing (@ {datetime.datetime.now()})")

        # TODO what we read from .joy() is not up to date as drip() hasn't happened!!
        joy_in_sai = self.tub.joy()
        woe_in_sai = self.tub.woe()
        mendable_amount = Wad.min(joy_in_sai, woe_in_sai)

        print(f"Joy (before mending): {joy_in_sai} SAI")
        print(f"Woe (before mending): {woe_in_sai} SAI")

        price_eth_skr = self.tub.per()
        price_sai_eth = self.tub.tag()
        price_sai_skr = price_eth_skr * price_sai_eth

        joy_in_sai -= mendable_amount
        woe_in_sai -= mendable_amount
        joy_in_skr = joy_in_sai/price_sai_skr
        woe_in_skr = Wad.from_number(woe_in_sai / price_sai_skr)

        print(f"Joy: {joy_in_sai} SAI (= {joy_in_skr} SKR)")
        print(f"Woe: {woe_in_sai} SAI (= {woe_in_skr} SKR)")
        print(f"SAI/SKR price: {price_sai_skr}")

        min_order_size_in_sai = Wad.from_number(5)
        min_order_size_in_skr = Wad.from_number(min_order_size_in_sai / price_sai_skr)

        print(f"Minimum processable size in SAI: {min_order_size_in_sai} SAI")
        print(f"Minimum processable size in SKR: {min_order_size_in_skr} SKR")

        # We do not process anything if below limits
        if woe_in_sai < min_order_size_in_sai or woe_in_skr < min_order_size_in_skr:
            print("No woe() or woe() below minimum limits, will not process anything.")
            return

        our_skr_balance = self.skr.balance_of(self.our_address)
        if our_skr_balance < min_order_size_in_skr:
            print(f"The amount of SKR in our account ({our_skr_balance} SKR) is below minimum limit, will not process anything.")
            return

        # Processing `woe_in_sai` (`bust`) means selling SAI to the Tub in return of SKR.
        # Calling 'bust' will perform the exchange using the `price_sai_skr` price.
        #
        # Our keeper only does it if we have a matching order on OasisDEX, which
        # allows us to buy SAI cheaper. If we find such order, we first buy SAI
        # on OasisDEX, if the trade is successfull we call `bust` to receive SKR.
        # If it's still not too late for `bust`, the amount of SKR received
        # from the `Tub` should be greater than the original SKR amount invested
        # in the trade. If somebody managed to call `bust` earlier than us,
        # we end up with some extra SAI which we think it's not too bad.

        price_limit = price_sai_skr * (1 + 0.001)
        print(f"Tub performs bust() at {price_sai_skr} SAI/SKR")
        print(f"Looking for a SAI sell offer on OasisDEX with price at least {price_limit} SAI/SKR")

        # We list all active orders on OasisDEX and filter on the SAI/SKR pair
        offers = self.all_offers(self.market)
        offers = self.filter_by_token_pair(offers, self.sai, self.skr)

        # We remove offers below our minimal limits
        offers = filter(lambda offer: offer.sell_how_much >= min_order_size_in_sai, offers)
        offers = filter(lambda offer: offer.buy_how_much >= min_order_size_in_skr, offers)

        # We only leave offers that are above the price limit
        offers = filter(lambda offer: self.sell_to_buy_price(offer) > price_limit, offers)

        # We sort them descending by price and we take the first one
        # ie. the one that will give us the greatest amount of SAI for SKR
        offers = sorted(offers, key=lambda offer: self.sell_to_buy_price(offer), reverse=True)
        best_offer = self.first_offer(offers)

        # If no single offer found, we do not process
        if best_offer is None:
            print("No attractive enough offer found on OasisDEX, will not process anything.")
            return

        print(f"Found offer #{best_offer.offer_id} with price {self.sell_to_buy_price(best_offer)} SAI/SKR")

        # Perform SKR to SAI exchange on OasisDEX
        offer_skr = Wad.min(woe_in_skr, Wad.min(best_offer.buy_how_much, our_skr_balance))
        offer_sai = Wad(offer_skr * self.sell_to_buy_price(best_offer))

        print(f"--- Phase 1 (taking the offer on OasisDEX) ---")
        print(f"Taking quantity={offer_sai} of offer #{best_offer.offer_id}")
        print(f"This should get us {offer_sai} SAI for {offer_skr} SKR")

        take_result = self.market.take(best_offer.offer_id, offer_sai)
        if not take_result:
            print(best_offer)
            print(f"Failed to take quantity={offer_sai} of offer #{best_offer.offer_id} failed, will not carry on")
            exit(-1)
            return

        skr_transfer_on_take = next(filter(lambda transfer: transfer.token_address == self.skr.address and transfer.from_address == self.our_address, take_result.transfers))
        sai_transfer_on_take = next(filter(lambda transfer: transfer.token_address == self.sai.address and transfer.to_address == self.our_address, take_result.transfers))

        print(f"Take was successful, we received {sai_transfer_on_take.wad} SAI for {skr_transfer_on_take.wad} SKR")


        # Perform SAI to SKR exchange on Tub by calling bust()
        bust_sai = Wad.min(woe_in_sai, sai_transfer_on_take.wad)
        bust_skr = Wad.min(woe_in_skr, Wad.from_number(bust_sai / price_sai_skr))

        print(f"--- Phase 2 (performing bust() on Tub) ---")
        print(f"Calling bust() with {bust_skr} which should take {bust_sai} SAI from us and give us {bust_skr} SKR")

        bust_result = self.tub.bust(bust_skr)
        if not bust_result:
            print(f"Failed to call bust() with {bust_skr}, we ended up with {sai_transfer_on_take.wad} extra SAI...")
            return

        skr_transfer_on_bust = next(filter(lambda transfer: transfer.token_address == self.skr.address and transfer.to_address == self.our_address, bust_result.transfers))
        sai_transfer_on_bust = next(filter(lambda transfer: transfer.token_address == self.sai.address and transfer.from_address == self.our_address, bust_result.transfers))

        print(f"Successfully called bust(), we got {skr_transfer_on_bust.wad} SKR for {sai_transfer_on_bust.wad} SAI")
        print(f"It all means we made a profit of {skr_transfer_on_bust.wad - skr_transfer_on_take.wad} SKR")

    def run(self):
        parser = argparse.ArgumentParser(description='SaiProcessWoe keeper..')
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--eth-from", help="Ethereum account from which to send transactions", required=True, type=str)
        parser.add_argument("--frequency", help="Frequency of checking for arbitrage opportunities (default: 5)", default=5, type=float)
        args = parser.parse_args()

        config = Config()

        web3 = Web3(HTTPProvider(endpoint_uri=f"http://{args.rpc_host}:{args.rpc_port}"))
        web3.eth.defaultAccount = args.eth_from #TODO allow to use ETH_FROM env variable

        self.our_address = Address(args.eth_from)
        self.tub_address = Address(config.get_contract_address("saiTub"))
        self.tub = Tub(web3=web3, address=self.tub_address)
        self.tip = DSValue(web3=web3, address=self.tub.tip())
        self.skr = ERC20Token(web3=web3, address=self.tub.skr())
        self.sai = ERC20Token(web3=web3, address=self.tub.sai())

        self.market_address = Address(config.get_contract_address("otc"))
        self.market = SimpleMarket(web3=web3, address=self.market_address)

        print(f"")
        print(f"SaiProcessWoe keeper")
        print(f"--------------------")

        while True:
            self.process()
            time.sleep(5)


if __name__ == '__main__':
    SaiProcessWoe().run()
