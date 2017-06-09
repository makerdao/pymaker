# This file is part of "maker.py".
# Copyright (C) 2017 MakerDAO
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


class SimpleMarket:
    def __init__(self, web3, address):
        Market = web3.eth.contract(abi=abi, bytecode=bytecode)
        self.contract = Market(address=address)

        self.state = {}

    def make(self, have_token, want_token, have_amount, want_amount):
        return self.contract.transact().make(have_token,
                                             want_token,
                                             have_amount,
                                             want_amount)

    def take(self, id, quantity):
        self.contract.transact().take(id, quantity)

    def kill(self, id):
        self.contact.transact().kill(id)

    def reconstruct(self):
        """Scan over the event history and determine the current
        state of the order book.
        """
