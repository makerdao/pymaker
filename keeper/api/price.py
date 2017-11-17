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

from typing import Optional

from keeper import Wad
from keeper.api.feed import DSValue
from keeper.api.sai import Tub


class PriceFeed(object):
    def get_price(self) -> Optional[Wad]:
        raise NotImplementedError("Please implement this method")


class TubPriceFeed(PriceFeed):
    def __init__(self, tub: Tub):
        self.tub = tub
        self.ds_value = DSValue(web3=self.tub.web3, address=self.tub.pip())

    def get_price(self) -> Optional[Wad]:
        return Wad(self.ds_value.read_as_int()) / self.tub.par()
