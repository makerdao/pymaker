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

import json

import pkg_resources
import pytest
from mock import Mock
from web3 import EthereumTesterProvider, Web3, HTTPProvider

from pymaker import Address
from pymaker.approval import directly
from pymaker.deployment import deploy_contract
from pymaker.numeric import Wad
from pymaker.token import DSToken, ERC20Token
from pymaker.util import bytes_to_hexstring
from pymaker.zrxv2 import ZrxExchangeV2, Order, ZrxRelayerApi
from tests.helpers import is_hashable, wait_until_mock_called

PAST_BLOCKS = 100


web3 = Web3(HTTPProvider('http://localhost:8545'))
exchange = ZrxExchangeV2(web3=web3, address=Address('0x4f833a24e1f95d70f028921e27040ca56e09ab0b'))


print(exchange.past_fill(18000))
