# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2019-2021 EdNoepel
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

import logging

from pymaker import Address, Contract
from pymaker.approval import directly, hope_directly
from pymaker.auctions import AuctionContract, Clipper, Flipper
from pymaker.ilk import Ilk
from pymaker.gas import DefaultGasPrice
from pymaker.join import GemJoin
from pymaker.token import DSToken, ERC20Token


logger = logging.getLogger()


class Collateral:
    """The `Collateral` object wraps accounting information in the Ilk with token-wide artifacts shared across
    multiple collateral types for the same token.  For example, ETH-A and ETH-B are represented by different Ilks,
    but will share the same gem (WETH token), GemJoin instance, and Flipper contract.
    """

    def __init__(self, ilk: Ilk, gem: ERC20Token, adapter: GemJoin, auction: AuctionContract, pip, vat: Contract):
        assert isinstance(ilk, Ilk)
        assert isinstance(gem, ERC20Token)
        assert isinstance(adapter, GemJoin)
        assert isinstance(auction, AuctionContract)
        assert isinstance(vat, Contract)

        self.ilk = ilk
        self.gem = gem
        self.adapter = adapter
        if isinstance(auction, Flipper):
            self.flipper = auction
            self.clipper = None
        elif isinstance(auction, Clipper):
            self.flipper = None
            self.clipper = auction
        # Points to `median` for official deployments, `DSValue` for testing purposes.
        # Users generally have no need to interact with the pip.
        self.pip = pip
        self.vat = vat

    def approve(self, usr: Address, **kwargs):
        """
        Allows the user to move this collateral into and out of their CDP.

        Args
            usr: User making transactions with this collateral
        """
        gas_strategy = kwargs['gas_strategy'] if 'gas_strategy' in kwargs else DefaultGasPrice()
        self.adapter.approve(hope_directly(from_address=usr, gas_strategy=gas_strategy), self.vat.address)
        self.adapter.approve_token(directly(from_address=usr, gas_strategy=gas_strategy))
