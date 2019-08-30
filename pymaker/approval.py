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

import logging

from pymaker import Address, Contract
from pymaker.numeric import Wad
from pymaker.token import ERC20Token
from pymaker.transactional import TxManager


def directly(**kwargs):
    """Approval function: Approves the caller to access tokens directly.

    This function is meant to be passed as a parameter to the `approve(...)` method
    of `Tub`, `SimpleMarket`, 'EtherDelta', 'TxManager', `ZrxExchange` and possibly
    others in the future.
    """

    def approval_function(token: ERC20Token, spender_address: Address, spender_name: str):
        address_to_check = kwargs['from_address'] if 'from_address' in kwargs else Address(token.web3.eth.defaultAccount)

        if token.allowance_of(address_to_check, spender_address) < Wad(2 ** 128 - 1):
            logger = logging.getLogger()
            logger.info(f"Approving {spender_name} ({spender_address}) to access our {token.address} directly")
            if not token.approve(spender_address).transact(**kwargs):
                raise RuntimeError("Approval failed!")

    return approval_function


def via_tx_manager(tx_manager: TxManager, **kwargs):
    """Approval function: Approves the caller to access tokens via the `TxManager`.

    This function is meant to be passed as a parameter to the `approve(...)` method
    of `Tub`, `SimpleMarket`, 'EtherDelta', 'TxManager', `ZrxExchange` and possibly
    others in the future.
    """
    assert(isinstance(tx_manager, TxManager))

    def approval_function(token: ERC20Token, spender_address: Address, spender_name: str):
        if token.allowance_of(tx_manager.address, spender_address) < Wad(2 ** 128 - 1):
            logger = logging.getLogger()
            logger.info(f"Approving {spender_name} ({spender_address}) to access our {token.address}"
                        f" via TxManager {tx_manager.address}")
            if not tx_manager.execute([], [(token.approve(spender_address).invocation())]).transact(**kwargs):
                raise RuntimeError("Approval failed!")

    return approval_function


def hope_directly(**kwargs):
    """Approval function: Approves the caller to access tokens directly.

    This function is meant to be passed as a parameter to the `approve(...)` method
    of `Flipper` and `Flopper` and possibly others in the future.
    """

    move_abi = [{'constant': False, 'inputs': [{'name': 'guy', 'type': 'address'}], 'name': 'hope', 'outputs': [],
                 'payable': False, 'stateMutability': 'nonpayable', 'type': 'function'},
                {'constant': True, 'inputs': [{'name': '', 'type': 'address'}, {'name': '', 'type': 'address'}],
                 'name': 'can', 'outputs': [{'name': '', 'type': 'bool'}], 'payable': False, 'stateMutability': 'view',
                 'type': 'function'}]

    def approval_function(token: ERC20Token, spender_address: Address, spender_name: str):
        address_to_check = kwargs['from_address'] if 'from_address' in kwargs else Address(
            token.web3.eth.defaultAccount)

        transact_args = {'from': address_to_check.address}

        move_contract = Contract._get_contract(web3=token.web3, abi=move_abi, address=token.address)
        if move_contract.call().can(address_to_check.address, spender_address.address) is False:
            logger = logging.getLogger()
            logger.info(f"Approving {spender_name} ({spender_address}) to move our {token.address} directly")
            if not move_contract.functions.hope(spender_address.address).transact(transact_args):
                raise RuntimeError("Approval failed!")

    return approval_function
