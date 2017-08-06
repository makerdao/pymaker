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

import pkg_resources
import pytest
from web3 import EthereumTesterProvider
from web3 import Web3

from api import Address
from api import Wad
from api.approval import directly
from api.auth import DSGuard
from api.feed import DSValue
from api.sai import Tub, Tap, Top
from api.token import DSToken
from api.vault import DSVault


class SaiDeployment:
    def __init__(self,
                 web3: Web3,
                 our_address: Address,
                 gem: DSToken,
                 sai: DSToken,
                 skr: DSToken,
                 tub: Tub,
                 tap: Tap,
                 top: Top):
        self.web3 = web3
        self.our_address = our_address
        self.gem = gem
        self.sai = sai
        self.skr = skr
        self.tub = tub
        self.tap = tap
        self.top = top


@pytest.fixture(scope='session')
def new_sai() -> SaiDeployment:
    def deploy(web3, contract_name, args=None):
        contract_factory = web3.eth.contract(abi=json.loads(pkg_resources.resource_string('api.feed', f'abi/{contract_name}.abi')),
                                             bytecode=pkg_resources.resource_string('api.feed', f'abi/{contract_name}.bin'))
        tx_hash = contract_factory.deploy(args=args)
        receipt = web3.eth.getTransactionReceipt(tx_hash)
        return receipt['contractAddress']

    web3 = Web3(EthereumTesterProvider())
    web3.eth.defaultAccount = web3.eth.accounts[0]
    our_address = Address(web3.eth.defaultAccount)
    sai = DSToken.deploy(web3, 'SAI')
    sin = DSToken.deploy(web3, 'SIN')
    gem = DSToken.deploy(web3, 'ETH')
    pip = DSValue.deploy(web3)
    skr = DSToken.deploy(web3, 'SKR')
    pot = DSVault.deploy(web3)
    pit = DSVault.deploy(web3)
    tip = deploy(web3, 'Tip')
    dad = DSGuard.deploy(web3)
    jug = deploy(web3, 'SaiJug', [sai.address.address, sin.address.address])
    jar = deploy(web3, 'SaiJar', [skr.address.address, gem.address.address, pip.address.address])

    tub = Tub.deploy(web3, Address(jar), Address(jug), pot.address, pit.address, Address(tip))
    tap = Tap.deploy(web3, tub.address, pit.address)
    top = Top.deploy(web3, tub.address, tap.address)

    # set permissions
    dad.permit(DSGuard.ANY, DSGuard.ANY, DSGuard.ANY)
    for auth in [sai, sin, skr, pot, pit, tub, tap, top]:
        auth.set_authority(dad.address)

    # approve, mint some GEMs
    tub.approve(directly())
    gem.mint(Wad.from_number(1000000)).transact()

    web3.currentProvider.rpc_methods.evm_snapshot()
    return SaiDeployment(web3, our_address, gem, sai, skr, tub, tap, top)


@pytest.fixture()
def sai(new_sai: SaiDeployment) -> SaiDeployment:
    new_sai.web3.currentProvider.rpc_methods.evm_revert()
    new_sai.web3.currentProvider.rpc_methods.evm_snapshot()
    return new_sai
