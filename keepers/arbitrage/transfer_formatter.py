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

import itertools
from functools import reduce
from typing import Iterable

from api.Address import Address
from api.token import ERC20Token
from api.Transfer import Transfer
from api.numeric import Wad


class TransferFormatter:
    def _sum(self, wads):
        return reduce(Wad.__add__, wads, Wad.from_number(0))

    def _sum_by_token(self, transfers: list):
        transfers.sort(key=lambda transfer: transfer.token_address, reverse=False)
        for token_address, transfers in itertools.groupby(transfers, lambda transfer: transfer.token_address):
            total = self._sum(map(lambda transfer: transfer.value, transfers))
            yield f"{total} {ERC20Token.token_name_by_address(token_address)}"

    def _net_value(self, transfer: Transfer, our_address: Address):
        if transfer.from_address == our_address and transfer.to_address == our_address:
            return Wad(0)
        elif transfer.from_address == our_address:
            return Wad(0) - transfer.value
        elif transfer.to_address == our_address:
            return transfer.value
        else:
            return Wad(0)

    def _net_by_token(self, transfers: list, our_address: Address):
        transfers.sort(key=lambda transfer: transfer.token_address, reverse=False)
        for token_address, transfers in itertools.groupby(transfers, lambda transfer: transfer.token_address):
            total = self._sum(map(lambda transfer: self._net_value(transfer, our_address), transfers))
            yield f"{total} {ERC20Token.token_name_by_address(token_address)}"

    def _join_with_and(self, iterable: Iterable):
        return " and ".join(iterable)

    def format(self, transfers: Iterable):
        return self._join_with_and(self._sum_by_token(list(transfers)))

    def format_net(self, transfers: Iterable, our_address: Address):
        return self._join_with_and(self._net_by_token(list(transfers), our_address))
