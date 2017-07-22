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

import logging
from web3 import HTTPProvider
from web3 import Web3

from api import Address, Wad
from api.approval import directly
from api.etherdelta import EtherDelta, OnChainOrder
from api.token import ERC20Token


logging_format = '%(asctime)-15s %(levelname)-8s %(name)-6s %(message)s'
logging.basicConfig(format=logging_format, level=logging.INFO)

# web3 = Web3(HTTPProvider(endpoint_uri=f"http://localhost:9545")) #mainnet
web3 = Web3(HTTPProvider(endpoint_uri=f"http://localhost:8545")) #kovan
web3.eth.defaultAccount = '0x002ca7F9b416B2304cDd20c26882d1EF5c53F611'

our_address = Address(web3.eth.defaultAccount)

# etherdelta_address = Address('0x8d12A197cB00D4747a1fe03395095ce2A5CC6819') #mainnet
etherdelta_address = Address('0xF4Ff487adA7bb29603077216082DA7f4bA989854') #kovan
etherdelta = EtherDelta(web3, etherdelta_address)

sai = ERC20Token(web3=web3, address=Address('0xb3e5b1e7fa92f827bdb79063df9173fefd07689d'))
gem = ERC20Token(web3=web3, address=Address('0x53eccc9246c1e537d79199d0c7231e425a40f896'))

etherdelta.approve([sai, gem], directly())

# print(len(etherdelta.active_onchain_orders()))
# exit(-1)
#
# etherdelta.deposit_token(sai.address, Wad.from_number(0.5))
# etherdelta.withdraw_token(sai.address, Wad.from_number(0.4))
# logging.info(etherdelta.balance_of_token(sai.address, our_address))

# etherdelta.deposit(Wad.from_number(0.1))
# etherdelta.withdraw(Wad.from_number(0.01))
# logging.info(etherdelta.balance_of(our_address))

logging.info(etherdelta.admin())
logging.info(etherdelta.fee_account())
logging.info(etherdelta.fee_make())
logging.info(etherdelta.fee_take())
logging.info(etherdelta.fee_rebate())
# logging.info(etherdelta.deposit_token(gem.address, Wad.from_number(0.01)))
logging.info(etherdelta.balance_of_token(gem.address, our_address))
logging.info(etherdelta.balance_of_token(sai.address, our_address))

logging.info("---")

# offchain_order = etherdelta.place_order_offchain(gem.address, Wad.from_number(0.0025), sai.address, Wad.from_number(0.1),
#                                            3600002)
# logging.info(offchain_order)
# logging.info(etherdelta.amount_available(offchain_order))
# logging.info(etherdelta.amount_filled(offchain_order))
# logging.info(etherdelta.can_trade(offchain_order, Wad.from_number(0.0026)))
# logging.info(etherdelta.can_trade(offchain_order, Wad.from_number(0.0025)))
# logging.info(etherdelta.can_trade(offchain_order, Wad.from_number(0.0006)))
# logging.info(etherdelta.trade(offchain_order, Wad.from_number(0.0006)))
# logging.info(etherdelta.amount_available(offchain_order))
# logging.info(etherdelta.amount_filled(offchain_order))
# logging.info(etherdelta.cancel_order(offchain_order))
# logging.info(etherdelta.amount_available(offchain_order))
# logging.info(etherdelta.amount_filled(offchain_order))
#
# logging.info("---")

logging.info(len(etherdelta.active_onchain_orders()))
logging.info(etherdelta.place_order_onchain(gem.address, Wad.from_number(0.0025), sai.address, Wad.from_number(0.1), 3600003))
onchain_order = OnChainOrder(gem.address, Wad.from_number(0.0025), sai.address, Wad.from_number(0.1), 3600003, 108207123768469167288277382516046143893265072544230933698775098822034023113615, our_address)
logging.info(len(etherdelta.active_onchain_orders()))
logging.info(onchain_order)
logging.info(etherdelta.amount_available(onchain_order))
logging.info(etherdelta.amount_filled(onchain_order))
logging.info(len(etherdelta.active_onchain_orders()))
logging.info(etherdelta.cancel_order(onchain_order))
logging.info(etherdelta.amount_available(onchain_order))
logging.info(etherdelta.amount_filled(onchain_order))
logging.info(len(etherdelta.active_onchain_orders()))

