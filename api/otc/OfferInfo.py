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

import datetime
from pprint import pformat

from api.Address import Address
from api.Wad import Wad
from api.token.ERC20Token import ERC20Token


class OfferInfo:
    """Represents a single offer on `SimpleMarket` (`OasisDEX`).

    Attributes:
        offer_id: Id of the offer.
        sell_how_much: The amount of the `sell_which_token` token which is put on sale.
        sell_which_token: The token which is put on sale.
        buy_how_much: The price the offer creator wants to be paid, denominated in the `buy_which_token` token.
        buy_which_token: The token the offer creator wants to be paid with.
        owner: Ethereum address of the owner of this offer.
        active: Flag whether this offer is active or not. Actually it is always `True`.
        timestamp: Date and time when this offer has been created.
    """

    def __init__(self, offer_id: int, sell_how_much: Wad, sell_which_token: ERC20Token, buy_how_much: Wad,
                 buy_which_token: ERC20Token, owner: Address, active: bool, timestamp: datetime):
        self.offer_id = offer_id
        self.sell_how_much = sell_how_much
        self.sell_which_token = sell_which_token
        self.buy_how_much = buy_how_much
        self.buy_which_token = buy_which_token
        self.owner = owner
        self.active = active
        self.timestamp = timestamp

    def __eq__(self, other):
        return self.offer_id == other.offer_id

    def __str__(self):
        return pformat(vars(self))
