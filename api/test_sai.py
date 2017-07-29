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

import json

import pkg_resources
import pytest
from web3 import Web3, EthereumTesterProvider

from api import Address, Wad
from api.approval import directly
from api.auth import DSGuard
from api.feed import DSValue
from api.numeric import Ray
from api.sai import Tub, Top, Tap
from api.token import DSToken
from api.vault import DSVault


class SaiDeployment:
    def __init__(self):
        pass


class TestSai():
    @pytest.fixture(scope='session')
    def new_deployment(self) -> SaiDeployment:
        state = SaiDeployment()
        state.provider = EthereumTesterProvider()
        state.web3 = Web3(state.provider)
        state.web3.eth.defaultAccount = state.web3.eth.accounts[0]
        state.our_address = Address(state.web3.eth.defaultAccount)
        state.sai = DSToken.deploy(state.web3, 'SAI')
        state.sin = DSToken.deploy(state.web3, 'SIN')
        state.gem = DSToken.deploy(state.web3, 'ETH')
        state.pip = DSValue.deploy(state.web3)
        state.skr = DSToken.deploy(state.web3, 'SKR')
        state.pot = DSVault.deploy(state.web3)
        state.pit = DSVault.deploy(state.web3)
        state.tip = self.deploy(state.web3, 'Tip')
        state.dad = DSGuard.deploy(state.web3)
        state.jug = self.deploy(state.web3, 'SaiJug', [state.sai.address.address, state.sin.address.address])
        state.jar = self.deploy(state.web3, 'SaiJar', [state.skr.address.address, state.gem.address.address, state.pip.address.address])
        state.tub = Tub.deploy(state.web3, Address(state.jar), Address(state.jug), state.pot.address, state.pit.address, Address(state.tip))
        state.tap = Tap.deploy(state.web3, state.tub.address, state.pit.address)
        state.top = Top.deploy(state.web3, state.tub.address, state.tap.address)

        # set permissions
        state.dad.permit(DSGuard.ANY, DSGuard.ANY, DSGuard.ANY)
        for auth in [state.sai, state.sin, state.skr, state.pot, state.pit, state.tub, state.tap, state.top]:
            auth.set_authority(state.dad.address)

        # approve, mint some GEMs
        state.tub.approve(directly())
        state.gem.mint(Wad.from_number(1000000))

        state.provider.rpc_methods.evm_snapshot()
        return state

    @pytest.fixture()
    def sai_deployment(self, new_deployment) -> SaiDeployment:
        new_deployment.provider.rpc_methods.evm_revert()
        return new_deployment

    def deploy(self, web3, contract_name, args=None):
        contract_factory = web3.eth.contract(abi=json.loads(pkg_resources.resource_string('api.feed', f'abi/{contract_name}.abi')),
                                     bytecode=pkg_resources.resource_string('api.feed', f'abi/{contract_name}.bin'))
        tx_hash = contract_factory.deploy(args=args)
        receipt = web3.eth.getTransactionReceipt(tx_hash)
        return receipt['contractAddress']

    def test_join_and_exit(self, sai_deployment):
        # given
        assert sai_deployment.skr.balance_of(sai_deployment.our_address) == Wad(0)
        assert sai_deployment.skr.total_supply() == Wad(0)

        # when
        print(sai_deployment.tub.join(Wad.from_number(5)))

        # then
        assert sai_deployment.skr.balance_of(sai_deployment.our_address) == Wad.from_number(5)
        assert sai_deployment.skr.total_supply() == Wad.from_number(5)

        # when
        print(sai_deployment.tub.exit(Wad.from_number(4)))

        # then
        assert sai_deployment.skr.balance_of(sai_deployment.our_address) == Wad.from_number(1)
        assert sai_deployment.skr.total_supply() == Wad.from_number(1)

    def test_cork_and_hat(self, sai_deployment):
        # given
        assert sai_deployment.tub.hat() == Wad(0)

        # when
        print(sai_deployment.tub.cork(Wad.from_number(150000)))

        # then
        assert sai_deployment.tub.hat() == Wad.from_number(150000)

    def test_crop_and_tax(self, sai_deployment):
        # given
        assert sai_deployment.tub.tax() == Ray.from_number(1)

        # when
        print(sai_deployment.tub.crop(Ray.from_number(1.00000000000000002)))

        # then
        assert sai_deployment.tub.tax() == Ray.from_number(1.00000000000000002)
