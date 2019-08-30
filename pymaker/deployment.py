# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus, bargst
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

import eth_utils
import json
import os
import re
from typing import Dict, List, Optional

import pkg_resources
from pymaker.auctions import Flapper, Flopper, Flipper
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.approval import directly, hope_directly
from pymaker.auth import DSGuard
from pymaker.etherdelta import EtherDelta
from pymaker.dss import Vat, Spotter, Vow, Jug, Cat, Collateral, DaiJoin, Ilk, GemJoin
from pymaker.feed import DSValue
from pymaker.governance import DSPause
from pymaker.numeric import Wad, Ray
from pymaker.oasis import MatchingMarket
from pymaker.sai import Tub, Tap, Top, Vox
from pymaker.token import DSToken, DSEthToken
from pymaker.vault import DSVault


def deploy_contract(web3: Web3, contract_name: str, args: Optional[list] = None) -> Address:
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
    bytecode = str(pkg_resources.resource_string('pymaker.deployment', f'abi/{contract_name}.bin'), 'utf-8')
    if args is not None:
        tx_hash = web3.eth.contract(abi=abi, bytecode=bytecode).constructor(*args).transact()
    else:
        tx_hash = web3.eth.contract(abi=abi, bytecode=bytecode).constructor().transact()
    receipt = web3.eth.getTransactionReceipt(tx_hash)
    return Address(receipt['contractAddress'])


class Deployment:
    """Represents a test deployment of the Maker smart contract ecosystem for single collateral Dai (SCD).

    Creating an instance of this class creates a testrpc web3 provider with the entire set
    of Maker smart contracts deployed to it. It is used in unit tests of PyMaker, and also in
    unit tests for individual keepers.
    """
    def __init__(self):
        web3 = Web3(HTTPProvider("http://localhost:8555"))
        web3.eth.defaultAccount = web3.eth.accounts[0]
        our_address = Address(web3.eth.defaultAccount)
        sai = DSToken.deploy(web3, 'DAI')
        sin = DSToken.deploy(web3, 'SIN')
        skr = DSToken.deploy(web3, 'PETH')
        gem = DSToken.deploy(web3, 'WETH')
        gov = DSToken.deploy(web3, 'MKR')
        pip = DSValue.deploy(web3)
        pep = DSValue.deploy(web3)
        pit = DSVault.deploy(web3)

        vox = Vox.deploy(web3, per=Ray.from_number(1))
        tub = Tub.deploy(web3, sai=sai.address, sin=sin.address, skr=skr.address, gem=gem.address, gov=gov.address,
                         pip=pip.address, pep=pep.address, vox=vox.address, pit=pit.address)
        tap = Tap.deploy(web3, tub.address)
        top = Top.deploy(web3, tub.address, tap.address)

        tub._contract.transact().turn(tap.address.address)

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
        tub.set_authority(dad.address).transact()
        for auth in [sai, sin, skr, gem, gov, pit, tap, top]:
            auth.set_authority(dad.address).transact()

        # whitelist pairs
        otc.add_token_pair_whitelist(sai.address, gem.address).transact()

        # approve
        tub.approve(directly())
        tap.approve(directly())

        # mint some GEMs
        gem.mint(Wad.from_number(1000000)).transact()

        self.snapshot_id = web3.manager.request_blocking("evm_snapshot", [])

        self.web3 = web3
        self.our_address = our_address
        self.sai = sai
        self.sin = sin
        self.skr = skr
        self.gem = gem
        self.gov = gov
        self.vox = vox
        self.tub = tub
        self.tap = tap
        self.top = top
        self.otc = otc
        self.etherdelta = etherdelta

    def reset(self):
        """Rollbacks all changes made since the initial deployment."""
        self.web3.manager.request_blocking("evm_revert", [self.snapshot_id])
        self.snapshot_id = self.web3.manager.request_blocking("evm_snapshot", [])

    def time_travel_by(self, seconds: int):
        assert(isinstance(seconds, int))
        self.web3.manager.request_blocking("evm_increaseTime", [seconds])


class DssDeployment:
    """Represents a Dai Stablecoin System deployment for multi-collateral Dai (MCD).

    Static method `from_json()` should be used to instantiate all the objet of
    a deployment from a json description of all the system addresses.
    """

    class Config:
        def __init__(self, pause: DSPause, vat: Vat, vow: Vow, jug: Jug, cat: Cat, flapper: Flapper,
                     flopper: Flopper, dai: DSToken, dai_join: DaiJoin, mkr: DSToken, spotter: Spotter,
                     collaterals: Optional[Dict[str, Collateral]] = None):
            self.pause = pause
            self.vat = vat
            self.vow = vow
            self.jug = jug
            self.cat = cat
            self.flapper = flapper
            self.flopper = flopper
            self.dai = dai
            self.dai_join = dai_join
            self.mkr = mkr
            self.spotter = spotter
            self.collaterals = collaterals or {}

        @staticmethod
        def from_json(web3: Web3, conf: str):
            conf = json.loads(conf)
            pause = DSPause(web3, Address(conf['MCD_PAUSE']))
            vat = Vat(web3, Address(conf['MCD_VAT']))
            vow = Vow(web3, Address(conf['MCD_VOW']))
            jug = Jug(web3, Address(conf['MCD_JUG']))
            cat = Cat(web3, Address(conf['MCD_CAT']))
            dai = DSToken(web3, Address(conf['MCD_DAI']))
            dai_adapter = DaiJoin(web3, Address(conf['MCD_JOIN_DAI']))
            flapper = Flapper(web3, Address(conf['MCD_FLAP']))
            flopper = Flopper(web3, Address(conf['MCD_FLOP']))
            mkr = DSToken(web3, Address(conf['MCD_GOV']))
            spotter = Spotter(web3, Address(conf['MCD_SPOT']))

            collaterals = {}
            for name in DssDeployment.Config._infer_collaterals_from_addresses(conf.keys()):
                ilk = Ilk(name[0].replace('_', '-'))
                if name[1] == "ETH":
                    gem = DSEthToken(web3, Address(conf[name[1]]))
                else:
                    gem = DSToken(web3, Address(conf[name[1]]))

                # TODO: If problematic, skip pip for deployments which use a medianizer.
                collateral = Collateral(ilk=ilk, gem=gem,
                                        adapter=GemJoin(web3, Address(conf[f'MCD_JOIN_{name[0]}'])),
                                        flipper=Flipper(web3, Address(conf[f'MCD_FLIP_{name[0]}'])),
                                        pip=DSValue(web3, Address(conf[f'PIP_{name[1]}'])))
                collaterals[ilk.name] = collateral

            return DssDeployment.Config(pause, vat, vow, jug, cat, flapper, flopper,
                                        dai, dai_adapter, mkr, spotter, collaterals)

        @staticmethod
        def _infer_collaterals_from_addresses(keys: []) -> List:
            collaterals = []
            for key in keys:
                match = re.search(r'MCD_FLIP_((\w+)_\w+)', key)
                if match:
                    collaterals.append((match.group(1), match.group(2)))
            return collaterals

        def to_dict(self) -> dict:
            conf_dict = {
                'MCD_PAUSE': self.pause.address.address,
                'MCD_VAT': self.vat.address.address,
                'MCD_VOW': self.vow.address.address,
                'MCD_JUG': self.jug.address.address,
                'MCD_CAT': self.cat.address.address,
                'MCD_FLAP': self.flapper.address.address,
                'MCD_FLOP': self.flopper.address.address,
                'MCD_DAI': self.dai.address.address,
                'MCD_JOIN_DAI': self.dai_join.address.address,
                'MCD_GOV': self.mkr.address.address,
                'MCD_SPOT': self.spotter.address.address
            }

            for collateral in self.collaterals.values():
                match = re.search(r'(\w+)-\w+', collateral.ilk.name)
                name = (collateral.ilk.name.replace('-', '_'), match.group(1))
                conf_dict[name[1]] = collateral.gem.address.address
                conf_dict[f'PIP_{name[1]}'] = collateral.pip.address.address
                conf_dict[f'MCD_JOIN_{name[0]}'] = collateral.adapter.address.address
                conf_dict[f'MCD_FLIP_{name[0]}'] = collateral.flipper.address.address

            return conf_dict

        def to_json(self) -> str:
            return json.dumps(self.to_dict())

    def __init__(self, web3: Web3, config: Config):
        assert isinstance(web3, Web3)
        assert isinstance(config, DssDeployment.Config)

        self.web3 = web3
        self.config = config
        self.pause = config.pause
        self.vat = config.vat
        self.vow = config.vow
        self.jug = config.jug
        self.cat = config.cat
        self.flapper = config.flapper
        self.flopper = config.flopper
        self.dai = config.dai
        self.dai_adapter = config.dai_join
        self.mkr = config.mkr
        self.collaterals = config.collaterals
        self.spotter = config.spotter

    @staticmethod
    def from_json(web3: Web3, conf: str):
        return DssDeployment(web3, DssDeployment.Config.from_json(web3, conf))

    def to_json(self) -> str:
        return self.config.to_json()

    @staticmethod
    def from_network(web3: Web3, network: str):
        assert isinstance(web3, Web3)
        assert isinstance(network, str)

        cwd = os.path.dirname(os.path.realpath(__file__))
        addresses_path = os.path.join(cwd, "../config", f"{network}-addresses.json")
        if not os.path.isfile(addresses_path):
            raise FileNotFoundError("Network is not yet supported")

        return DssDeployment.from_json(web3=web3, conf=open(addresses_path, "r").read())

    def approve_dai(self, usr: Address):
        """
        Allows the user to draw Dai from and repay Dai to their CDPs.

        Args
            usr: Recipient of Dai from one or more CDPs
        """
        assert isinstance(usr, Address)

        self.dai_adapter.approve(approval_function=hope_directly(from_address=usr), source=self.vat.address)
        self.dai.approve(self.dai_adapter.address).transact()

    def active_auctions(self) -> dict:
        flips = {}
        for collateral in self.collaterals.values():
            # Each collateral has it's own flip contract; add auctions from each.
            flips[collateral.ilk.name] = collateral.flipper.active_auctions()

        return {
            "flips": flips,
            "flaps": self.flapper.active_auctions(),
            "flops": self.flopper.active_auctions()
        }

    def __repr__(self):
        return f'DssDeployment({self.config.to_json()})'
