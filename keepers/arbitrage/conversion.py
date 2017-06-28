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

from api.Address import Address
from api.Ray import Ray
from api.Wad import Wad
from api.token.ERC20Token import ERC20Token


class Conversion:
    def __init__(self, source_token: Address, target_token: Address, rate: Ray, min_source_amount: Wad, max_source_amount: Wad, method: str):
        self.source_amount = None
        self.source_token = source_token
        self.target_amount = None
        self.target_token = target_token
        self.rate = rate
        self.min_source_amount = min_source_amount
        self.max_source_amount = max_source_amount
        self.method = method

    def name(self):
        raise NotImplementedError("name() not implemented")

    def execute(self):
        raise NotImplementedError("execute() not implemented")

    def __str__(self):
        def amt(amount: Wad) -> str:
            if amount is not None:
                return f"{amount} "
            else:
                return ""

        return f"[{amt(self.source_amount)}{ERC20Token.token_name_by_address(self.source_token)} -> {amt(self.target_amount)}{ERC20Token.token_name_by_address(self.target_token)} @{self.rate} " \
               f"by {self.method} (min={self.min_source_amount} {ERC20Token.token_name_by_address(self.source_token)}, max={self.max_source_amount} {ERC20Token.token_name_by_address(self.source_token)})]"
