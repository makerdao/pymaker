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
from typing import Optional

import pkg_resources
from web3 import Web3, EthereumTesterProvider

from pymaker import Address
from pymaker.approval import directly
from pymaker.auth import DSGuard
from pymaker.etherdelta import EtherDelta
from pymaker.feed import DSValue
from pymaker.numeric import Wad
from pymaker.oasis import MatchingMarket
from pymaker.sai import Tub, Tap, Top
from pymaker.token import DSToken
from pymaker.vault import DSVault


def deploy_contract(web3: Web3, contract_name: str, args: Optional[list]=None) -> Address:
    """Deploys a new contract.

    Args:
        web3: An instance of `Web` from `web3.py`.
        contract_name: Name of the contract, used to find the `abi` and `bin` files.
        args: Optional list of contract constructor parameters.

    Returns:
        Ethereum address of the newly deployed contract, as a :py:class:`pymaker.Address` instance.
    """
    assert(isinstance(web3, Web3))
    assert(isinstance(contract_name, str))
    assert(isinstance(args, list) or (args is None))

    abi = json.loads(pkg_resources.resource_string('pymaker.deployment', f'abi/{contract_name}.abi'))
    bytecode = pkg_resources.resource_string('pymaker.deployment', f'abi/{contract_name}.bin')
    tx_hash = web3.eth.contract(abi=abi, bytecode=bytecode).deploy(args=args)
    receipt = web3.eth.getTransactionReceipt(tx_hash)
    return Address(receipt['contractAddress'])


class Deployment:
    """Represents a test deployment of the entire Maker smart contract ecosystem.

    Creating an instance of this class creates a testrpc web3 provider with the entire set
    of Maker smart contracts deployed to it. It is used in unit tests of PyMaker, and also in
    unit tests for individual keepers.
    """
    def __init__(self):
        web3 = Web3(EthereumTesterProvider())
        web3.eth.defaultAccount = web3.eth.accounts[0]
        our_address = Address(web3.eth.defaultAccount)
        sai = DSToken.deploy(web3, 'SAI')
        sin = DSToken.deploy(web3, 'SIN')
        skr = DSToken.deploy(web3, 'SKR')
        gem = DSToken.deploy(web3, 'ETH')
        gov = DSToken.deploy(web3, 'MKR')
        pip = DSValue.deploy(web3)
        pep = DSValue.deploy(web3)
        pit = DSVault.deploy(web3)

        vox = deploy_contract(web3, 'SaiVox')
        tub = Tub.deploy(web3, sai=sai.address, sin=sin.address, skr=skr.address, gem=gem.address, gov=gov.address,
                         pip=pip.address, pep=pep.address, vox=vox, pit=pit.address)
        tap = Tap.deploy(web3, tub.address)
        top = Top.deploy(web3, tub.address, tap.address)

        otc = MatchingMarket.deploy(web3, 2600000000)
        etherdelta = EtherDelta.deploy(web3,
                                       admin=Address('0x1111100000999998888877777666665555544444'),
                                       fee_account=Address('0x8888877777666665555544444111110000099999'),
                                       account_levels_addr=Address('0x0000000000000000000000000000000000000000'),
                                       fee_make=Wad.from_number(0.01),
                                       fee_take=Wad.from_number(0.02),
                                       fee_rebate=Wad.from_number(0.03))

        # set permissions
        dad = DSGuard.deploy(web3)
        dad.permit(DSGuard.ANY, DSGuard.ANY, DSGuard.ANY).transact()
        tub.set_authority(dad.address)
        for auth in [sai, sin, skr, gem, gov, pit, tap, top]:
            auth.set_authority(dad.address).transact()

        # whitelist pairs
        otc.add_token_pair_whitelist(sai.address, gem.address).transact()

        # approve, mint some GEMs
        tub.approve(directly())
        gem.mint(Wad.from_number(1000000)).transact()

        web3.providers[0].rpc_methods.evm_snapshot()

        self.web3 = web3
        self.our_address = our_address
        self.sai = sai
        self.sin = sin
        self.skr = skr
        self.gem = gem
        self.gov = gov
        self.tub = tub
        self.tap = tap
        self.top = top
        self.otc = otc
        self.etherdelta = etherdelta

    def reset(self):
        """Rollbacks all changes made since the initial deployment."""
        self.web3.providers[0].rpc_methods.evm_revert()
        self.web3.providers[0].rpc_methods.evm_snapshot()
        self.otc._none_orders = set()
