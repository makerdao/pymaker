# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
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

import sys
import time

from web3 import EthereumTesterProvider, Web3, HTTPProvider

from pymaker import Address
from pymaker.approval import directly
from pymaker.numeric import Wad
from pymaker.token import DSToken, ERC20Token
from pymaker.util import bytes_to_hexstring
from pymaker.zrxv2 import ZrxExchangeV2, Order, ZrxRelayerApiV2, ERC20Asset
from tests.helpers import is_hashable, wait_until_mock_called

#EXCHANGE_ADDR = '0x4f833a24e1f95d70f028921e27040ca56e09ab0b'  # Mainnet
EXCHANGE_ADDR = sys.argv[1]
SRAV2_URL = 'https://kovan-staging.ercdex.com/api'

KOVAN_DAI = Address('0xc4375b7de8af5a38a93548eb8453a498222c4ff2')
KOVAN_WETH = Address('0xd0a1e359811322d97991e03f863a0c30c2cf029c')


web3 = Web3(HTTPProvider('http://localhost:8545'))
web3.eth.defaultAccount = web3.eth.accounts[0]

exchange = ZrxExchangeV2(web3=web3, address=Address(EXCHANGE_ADDR))
#exchange.approve([ERC20Token(web3=web3, address=KOVAN_DAI),
#                  ERC20Token(web3=web3, address=KOVAN_WETH)], directly())

order = exchange.create_order(pay_asset=ERC20Asset(KOVAN_WETH),
                              pay_amount=Wad.from_number(0.1),
                              buy_asset=ERC20Asset(KOVAN_DAI),
                              buy_amount=Wad.from_number(25),
                              expiration=int(time.time())+60*35)

api = ZrxRelayerApiV2(exchange=exchange, api_server=SRAV2_URL)
order = api.configure_order(order)
order = exchange.sign_order(order)
#print(order)

#print(api.submit_order(order))
#print(api.get_orders(KOVAN_WETH, KOVAN_DAI))
print(api.get_orders_by_maker(Address(web3.eth.defaultAccount)))

#print(exchange.past_fill(500))
