#!/usr/bin/env python3
#
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

from web3 import HTTPProvider
from web3 import Web3

from api import Address, Calldata
from api.token import ERC20Token
from api.sai import Tub
from api.transact import TxManager, Invocation

web3 = Web3(HTTPProvider(endpoint_uri=f"http://localhost:8545"))
web3.eth.defaultAccount = "0x002ca7F9b416B2304cDd20c26882d1EF5c53F611"

tub = Tub(web3=web3,
          address_tub=Address('0xc349a197c9c3200411094adec82972a2b921c6e2'),
          address_tap=Address('0x3d9a8aa3753bab869b1cc58063063773da54bd66'),
          address_top=Address('0x66174cf99acdb1a5568186a55827b2aac56275e1'))
sai = ERC20Token(web3=web3, address=tub.sai())
skr = ERC20Token(web3=web3, address=tub.skr())
gem = ERC20Token(web3=web3, address=tub.gem())


invocations = [Invocation(Address("0xdf3893359182f55b5f225e427c93ab3fcd48e967"),
                          Calldata('0x812600df0000000000000000000000000000000000000000000000000000000000000002')),
               Invocation(Address("0x89d88bf5cef2deac81b50b4c99f86c9437dce28f"),
                          Calldata('0x812600df0000000000000000000000000000000000000000000000000000000000000008'))]

tx = TxManager(web3=web3, address=Address("0x57bFE16ae8fcDbD46eDa9786B2eC1067cd7A8f48"))
receipt = tx.execute([sai.address, skr.address], invocations)
print(receipt.transaction_hash)
