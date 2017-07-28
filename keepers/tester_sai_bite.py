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
from web3 import Web3, EthereumTesterProvider, TestRPCProvider

from api import Address, Wad
from api.approval import directly
from api.auth import DSGuard
from api.feed import DSValue
from api.sai import Tub, Top, Tap
from api.token import DSToken
from api.vault import DSVault


class ExpTestSaiBite():
    def deploy(self, contract_name, args=None):
        contract_factory = self.web3.eth.contract(abi=json.loads(pkg_resources.resource_string('api.feed', f'abi/{contract_name}.abi')),
                                     bytecode=pkg_resources.resource_string('api.feed', f'abi/{contract_name}.bin'))
        tx_hash = contract_factory.deploy(args=args)
        receipt = self.web3.eth.getTransactionReceipt(tx_hash)
        return receipt['contractAddress']

    def run(self):
        self.web3 = Web3(EthereumTesterProvider())
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        our_account = Address(self.web3.eth.defaultAccount)

        sai = DSToken.deploy(self.web3, 'SAI')
        sin = DSToken.deploy(self.web3, 'SIN')
        gem = DSToken.deploy(self.web3, 'ETH')
        pip = DSValue.deploy(self.web3)
        skr = DSToken.deploy(self.web3, 'SKR')

        pot = DSVault.deploy(self.web3)
        pit = DSVault.deploy(self.web3)
        tip = self.deploy('Tip')

        dad = DSGuard.deploy(self.web3)

        jug = self.deploy('SaiJug', [sai.address.address, sin.address.address])
        jar = self.deploy('SaiJar', [skr.address.address, gem.address.address, pip.address.address])

        tub = Tub.deploy(self.web3, Address(jar), Address(jug), pot.address, pit.address, Address(tip))
        tap = Tap.deploy(self.web3, tub.address, pit.address)
        top = Top.deploy(self.web3, tub.address, tap.address)



        sai.set_authority(dad.address)
        sin.set_authority(dad.address)
        skr.set_authority(dad.address)
        pot.set_authority(dad.address)
        pit.set_authority(dad.address)
        top.set_authority(dad.address)


# seth send $SAI_TIP "warp(uint64)" 0
#
# seth send $SAI_TIP "setAuthority(address)" $SAI_MOM
# seth send $SAI_TUB "setAuthority(address)" $SAI_MOM
# seth send $SAI_TAP "setAuthority(address)" $SAI_MOM
# seth send $SAI_JAR "setAuthority(address)" $SAI_MOM
#
# seth send $SAI_JUG "setAuthority(address)" $SAI_DAD


        dad.permit(tub.address, Address(jug), DSGuard.ANY_SIG)
        dad.permit(tub.address, pot.address, DSGuard.ANY_SIG)

        dad.permit(tap.address, Address(jug), DSGuard.ANY_SIG)
        dad.permit(tap.address, pit.address, DSGuard.ANY_SIG)

        dad.permit(top.address, Address(jug), DSGuard.ANY_SIG)
        dad.permit(top.address, pit.address, DSGuard.ANY_SIG)

        dad.permit(Address(jar), skr.address, DSGuard.ANY_SIG)

        dad.permit(Address(jug), pot.address, DSGuard.ANY_SIG)
        dad.permit(Address(jug), pit.address, DSGuard.ANY_SIG)

        dad.permit(pot.address, sai.address, DSGuard.ANY_SIG)
        dad.permit(pot.address, sin.address, DSGuard.ANY_SIG)

        dad.permit(pit.address, sai.address, DSGuard.ANY_SIG)
        dad.permit(pit.address, sin.address, DSGuard.ANY_SIG)

        dad.permit(tub.address, tub.jar(), DSGuard.ANY_SIG)
        dad.permit(top.address, tub.jar(), DSGuard.ANY_SIG)
        dad.permit(top.address, tub.address, DSGuard.ANY_SIG)



        print(gem.balance_of(our_account))
        gem.mint(Wad.from_number(10))
        print(gem.balance_of(our_account))

        self.tub = tub




        # run test
        self.tub.approve(directly())
        self.tub.join(Wad.from_number(5))


        # pip_contract = DSValue(web3=self.web3, address=Address(pip))
        # print(pip_contract.has_value())
        # pip_contract.poke_with_int(12345)
        # print(pip_contract.has_value())
        # print(pip_contract.read_as_int())




# seth send $SAI_MOM "setRootUser(address,bool)" $ETH_FROM true && seth send $SAI_MOM "setAuthority(address)" $SAI_MOM
#
# export SETH_ASYNC=yes
#
# seth send $SAI_TIP "warp(uint64)" 0
#
# seth send $SAI_TIP "setAuthority(address)" $SAI_MOM
# seth send $SAI_TUB "setAuthority(address)" $SAI_MOM
# seth send $SAI_TAP "setAuthority(address)" $SAI_MOM
# seth send $SAI_TOP "setAuthority(address)" $SAI_MOM
# seth send $SAI_JAR "setAuthority(address)" $SAI_MOM
#
# seth send $SAI_POT "setAuthority(address)" $SAI_DAD
# seth send $SAI_PIT "setAuthority(address)" $SAI_DAD
# seth send $SAI_JUG "setAuthority(address)" $SAI_DAD
#
# seth send $SAI_SAI "setAuthority(address)" $SAI_DAD
# seth send $SAI_SIN "setAuthority(address)" $SAI_DAD
# seth send $SAI_SKR "setAuthority(address)" $SAI_DAD
#
# seth send $SAI_MOM "setUserRole(address,uint8,bool)" $SAI_TUB 255 true
# seth send $SAI_MOM "setRoleCapability(uint8,address,bytes4,bool)" 255 $SAI_JAR $(seth calldata 'join(address,uint128)') true
# seth send $SAI_MOM "setRoleCapability(uint8,address,bytes4,bool)" 255 $SAI_JAR $(seth calldata 'exit(address,uint128)') true
# seth send $SAI_MOM "setRoleCapability(uint8,address,bytes4,bool)" 255 $SAI_JAR $(seth calldata 'push(address,address,uint128)') true
# seth send $SAI_MOM "setRoleCapability(uint8,address,bytes4,bool)" 255 $SAI_JAR $(seth calldata 'pull(address,address,uint128)') true
#
# seth send $SAI_MOM "setUserRole(address,uint8,bool)" $SAI_TOP 254 true
# seth send $SAI_MOM "setRoleCapability(uint8,address,bytes4,bool)" 254 $SAI_JAR $(seth calldata 'push(address,address,uint128)') true
# seth send $SAI_MOM "setRoleCapability(uint8,address,bytes4,bool)" 254 $SAI_TUB $(seth calldata 'cage(uint128)') true
#



        # self.web3
        # print(self.web3.personal.listAccounts)
        # print(self.web3.eth.defaultAccount)


ExpTestSaiBite().run()
