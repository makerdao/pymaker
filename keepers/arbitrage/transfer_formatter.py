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

import copy
import operator
from functools import reduce
from typing import List

import itertools

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.token.ERC20Token import ERC20Token
from keepers.arbitrage.Conversion import Conversion


class TransferFormatter:
    def _sum_of_wads(self, list_of_wads):
        return reduce(Wad.__add__, list_of_wads, Wad.from_number(0))

    def _grouped_by_token(self, transfers):
        transfers.sort(key=lambda transfer: transfer.token_address, reverse=False)
        for token_address, transfers in itertools.groupby(transfers, lambda transfer: transfer.token_address):
            values = map(lambda transfer: transfer.value, transfers)
            sum_of_values = self._sum_of_wads(values)
            yield f"{sum_of_values} {ERC20Token.token_name_by_address(token_address)}"

    def format(self, transfers):
        return " and ".join(self._grouped_by_token(list(transfers)))
