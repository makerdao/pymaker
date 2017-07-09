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

from api import Address, Wad
from api.token import ERC20Token
from api.transact import TxManager, Invocation


def directly():
    def approval_function(token: ERC20Token, spender_address: Address, spender_name: str):
        if token.allowance_of(Address(token.web3.eth.defaultAccount), spender_address) < Wad(2 ** 128 - 1):
            logging.info(f"Approving {spender_name} ({spender_address}) to access our {token.name()} directly")
            if not token.approve(spender_address):
                raise RuntimeError("Approval failed!")

    return approval_function


def via_tx_manager(tx_manager: TxManager):
    def approval_function(token: ERC20Token, spender_address: Address, spender_name: str):
        if token.allowance_of(tx_manager.address, spender_address) < Wad(2 ** 128 - 1):
            logging.info(f"Approving {spender_name} ({spender_address}) to access our {token.name()}"
                         f" via TxManager {tx_manager.address}")
            invocation = Invocation(address=token.address, calldata=token.approve_calldata(spender_address))
            if not tx_manager.execute([], [invocation]):
                raise RuntimeError("Approval failed!")

    return approval_function
