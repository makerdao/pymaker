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

import json

from api.Address import Address
from api.token.ERC20Token import ERC20Token


class Config:
    def __init__(self):
        with open('keepers/addresses.json') as data_file:
            self.network = "kovan" #TODO implement network detection
            self.addresses = json.load(data_file)
        for key, value in self.addresses[self.network]["tokens"].items():
            ERC20Token.register_token(Address(value), key)

    def get_contract_address(self, name):
        return self.addresses[self.network]["contracts"][name]
