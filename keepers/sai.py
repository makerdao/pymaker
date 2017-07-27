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

from api import Address
from api.oasis import SimpleMarket
from api.sai import Tub, Top
from api.token import ERC20Token, DSEthToken
from keepers import Keeper


class SaiKeeper(Keeper):
    def __init__(self):
        super().__init__()
        self.tub_address = Address(self.config.get_contract_address("saiTub"))
        self.tap_address = Address(self.config.get_contract_address("saiTap"))
        self.tub = Tub(web3=self.web3, address_tub=self.tub_address, address_tap=self.tap_address)
        self.top_address = Address(self.config.get_contract_address("saiTop"))
        self.top = Top(web3=self.web3, address=self.top_address)
        self.otc_address = Address(self.config.get_contract_address("otc"))
        self.otc = SimpleMarket(web3=self.web3, address=self.otc_address)

        self.skr = ERC20Token(web3=self.web3, address=self.tub.skr())
        self.sai = ERC20Token(web3=self.web3, address=self.tub.sai())
        self.gem = DSEthToken(web3=self.web3, address=self.tub.gem())
        ERC20Token.register_token(self.tub.skr(), 'SKR')
        ERC20Token.register_token(self.tub.sai(), 'SAI')
        ERC20Token.register_token(self.tub.gem(), 'WETH')

    def startup(self):
        # implemented only to avoid IntelliJ IDEA warning
        super().startup()
