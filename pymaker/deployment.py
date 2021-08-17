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

import json
import os
import re
import time
import warnings
from typing import Dict, List, Optional

import pkg_resources
from pymaker.auctions import Clipper, Flapper, Flipper, Flopper
from web3 import Web3, HTTPProvider

from pymaker import Address, Contract
from pymaker.approval import directly, hope_directly
from pymaker.auth import DSGuard
from pymaker.etherdelta import EtherDelta
from pymaker.collateral import Collateral
from pymaker.dss import Cat, Dog, Jug, Pot, Spotter, TokenFaucet, Vat, Vow
from pymaker.join import DaiJoin, GemJoin, GemJoin5
from pymaker.proxy import ProxyRegistry, DssProxyActionsDsr
from pymaker.feed import DSValue
from pymaker.gas import DefaultGasPrice
from pymaker.governance import DSPause, DSChief
from pymaker.numeric import Wad, Ray
from pymaker.oracles import OSM
from pymaker.sai import Tub, Tap, Top, Vox
from pymaker.shutdown import ShutdownModule, End
from pymaker.token import DSToken, DSEthToken
from pymaker.vault import DSVault
from pymaker.cdpmanager import CdpManager
from pymaker.dsrmanager import DsrManager


def deploy_contract(web3: Web3, contract_name: str, args: Optional[list] = None) -> Address:
    warnings.warn("DEPRECATED: Please subclass Contract and call Contract._deploy instead.",
                  category=DeprecationWarning, stacklevel=2)
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
    return Contract._deploy(web3, abi, bytecode, args if args else [])


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

        tub._contract.functions.turn(tap.address.address).transact()

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

    NETWORKS = {
        "1": "mainnet",
        "42": "kovan"
    }

    class Config:
        def __init__(self, pause: DSPause, vat: Vat, vow: Vow, jug: Jug, cat: Cat, dog: Dog, flapper: Flapper,
                     flopper: Flopper, pot: Pot, dai: DSToken, dai_join: DaiJoin, mkr: DSToken,
                     spotter: Spotter, ds_chief: DSChief, esm: ShutdownModule, end: End,
                     proxy_registry: ProxyRegistry, dss_proxy_actions: DssProxyActionsDsr, cdp_manager: CdpManager,
                     dsr_manager: DsrManager, faucet: TokenFaucet, collaterals: Optional[Dict[str, Collateral]] = None):
            self.pause = pause
            self.vat = vat
            self.vow = vow
            self.jug = jug
            self.cat = cat
            self.dog = dog
            self.flapper = flapper
            self.flopper = flopper
            self.pot = pot
            self.dai = dai
            self.dai_join = dai_join
            self.mkr = mkr
            self.spotter = spotter
            self.ds_chief = ds_chief
            self.esm = esm
            self.end = end
            self.proxy_registry = proxy_registry
            self.dss_proxy_actions = dss_proxy_actions
            self.cdp_manager = cdp_manager
            self.dsr_manager = dsr_manager
            self.faucet = faucet
            self.collaterals = collaterals or {}

        @staticmethod
        def from_json(web3: Web3, conf: str):
            def address_in_configs(key: str, conf: str) -> bool:
                if key not in conf:
                    return False
                elif not conf[key]:
                    return False
                elif conf[key] == "0x0000000000000000000000000000000000000000":
                    return False
                else:
                    return True

            conf = json.loads(conf)
            pause = DSPause(web3, Address(conf['MCD_PAUSE']))
            vat = Vat(web3, Address(conf['MCD_VAT']))
            vow = Vow(web3, Address(conf['MCD_VOW']))
            jug = Jug(web3, Address(conf['MCD_JUG']))
            cat = Cat(web3, Address(conf['MCD_CAT'])) if address_in_configs('MCD_CAT', conf) else None
            dog = Dog(web3, Address(conf['MCD_DOG'])) if address_in_configs('MCD_DOG', conf) else None
            dai = DSToken(web3, Address(conf['MCD_DAI']))
            dai_adapter = DaiJoin(web3, Address(conf['MCD_JOIN_DAI']))
            flapper = Flapper(web3, Address(conf['MCD_FLAP']))
            flopper = Flopper(web3, Address(conf['MCD_FLOP']))
            pot = Pot(web3, Address(conf['MCD_POT']))
            mkr = DSToken(web3, Address(conf['MCD_GOV']))
            spotter = Spotter(web3, Address(conf['MCD_SPOT']))
            ds_chief = DSChief(web3, Address(conf['MCD_ADM']))
            esm = ShutdownModule(web3, Address(conf['MCD_ESM']))
            end = End(web3, Address(conf['MCD_END']))
            proxy_registry = ProxyRegistry(web3, Address(conf['PROXY_REGISTRY']))
            dss_proxy_actions = DssProxyActionsDsr(web3, Address(conf['PROXY_ACTIONS_DSR']))
            cdp_manager = CdpManager(web3, Address(conf['CDP_MANAGER']))
            dsr_manager = DsrManager(web3, Address(conf['DSR_MANAGER']))
            faucet = TokenFaucet(web3, Address(conf['FAUCET'])) if address_in_configs('FAUCET', conf) else None

            collaterals = {}
            for name in DssDeployment.Config._infer_collaterals_from_addresses(conf.keys()):
                ilk = vat.ilk(name[0].replace('_', '-'))
                if name[1] == "ETH":
                    gem = DSEthToken(web3, Address(conf[name[1]]))
                else:
                    gem = DSToken(web3, Address(conf[name[1]]))

                if name[1] in ['USDC', 'WBTC', 'TUSD', 'USDT', 'GUSD', 'RENBTC']:
                    adapter = GemJoin5(web3, Address(conf[f'MCD_JOIN_{name[0]}']))
                else:
                    adapter = GemJoin(web3, Address(conf[f'MCD_JOIN_{name[0]}']))

                # PIP contract may be a DSValue, OSM, or bogus address.
                pip_name = f'PIP_{name[1]}'
                pip_address = Address(conf[pip_name]) if pip_name in conf and conf[pip_name] else None
                val_name = f'VAL_{name[1]}'
                val_address = Address(conf[val_name]) if val_name in conf and conf[val_name] else None
                if pip_address:     # Configure OSM as price source
                    pip = OSM(web3, pip_address)
                elif val_address:   # Configure price using DSValue
                    pip = DSValue(web3, val_address)
                else:
                    pip = None

                auction = None
                if f'MCD_FLIP_{name[0]}' in conf:
                    auction = Flipper(web3, Address(conf[f'MCD_FLIP_{name[0]}']))
                elif f'MCD_CLIP_{name[0]}' in conf:
                    auction = Clipper(web3, Address(conf[f'MCD_CLIP_{name[0]}']))

                collateral = Collateral(ilk=ilk, gem=gem, adapter=adapter, auction=auction, pip=pip, vat=vat)
                collaterals[ilk.name] = collateral

            return DssDeployment.Config(pause, vat, vow, jug, cat, dog, flapper, flopper, pot,
                                        dai, dai_adapter, mkr, spotter, ds_chief, esm, end,
                                        proxy_registry, dss_proxy_actions, cdp_manager,
                                        dsr_manager, faucet, collaterals)

        @staticmethod
        def _infer_collaterals_from_addresses(keys: []) -> List:
            collaterals = []
            for key in keys:
                match = re.search(r'MCD_[CF]LIP_(?!CALC)((\w+)_\w+)', key)
                if match:
                    collaterals.append((match.group(1), match.group(2)))
                    continue
                match = re.search(r'MCD_[CF]LIP_(?!CALC)(\w+)', key)
                if match:
                    collaterals.append((match.group(1), match.group(1)))

            return collaterals

        def to_dict(self) -> dict:
            conf_dict = {
                'MCD_PAUSE': self.pause.address.address,
                'MCD_VAT': self.vat.address.address,
                'MCD_VOW': self.vow.address.address,
                'MCD_JUG': self.jug.address.address,
                'MCD_FLAP': self.flapper.address.address,
                'MCD_FLOP': self.flopper.address.address,
                'MCD_POT': self.pot.address.address,
                'MCD_DAI': self.dai.address.address,
                'MCD_JOIN_DAI': self.dai_join.address.address,
                'MCD_GOV': self.mkr.address.address,
                'MCD_SPOT': self.spotter.address.address,
                'MCD_ADM': self.ds_chief.address.address,
                'MCD_ESM': self.esm.address.address,
                'MCD_END': self.end.address.address,
                'PROXY_REGISTRY': self.proxy_registry.address.address,
                'PROXY_ACTIONS_DSR': self.dss_proxy_actions.address.address,
                'CDP_MANAGER': self.cdp_manager.address.address,
                'DSR_MANAGER': self.dsr_manager.address.address
            }

            if self.cat:
                conf_dict['MCD_CAT'] = self.cat.address.address
            if self.dog:
                conf_dict['MCD_DOG'] = self.dog.address.address
            if self.faucet:
                conf_dict['FAUCET'] = self.faucet.address.address

            for collateral in self.collaterals.values():
                match = re.search(r'(\w+)(?:-\w+)?', collateral.ilk.name)
                name = (collateral.ilk.name.replace('-', '_'), match.group(1))
                conf_dict[name[1]] = collateral.gem.address.address
                if collateral.pip:
                    conf_dict[f'PIP_{name[1]}'] = collateral.pip.address.address
                conf_dict[f'MCD_JOIN_{name[0]}'] = collateral.adapter.address.address
                if collateral.flipper:
                    conf_dict[f'MCD_FLIP_{name[0]}'] = collateral.flipper.address.address
                elif collateral.clipper:
                    conf_dict[f'MCD_CLIP_{name[0]}'] = collateral.clipper.address.address

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
        self.dog = config.dog
        self.flapper = config.flapper
        self.flopper = config.flopper
        self.pot = config.pot
        self.dai = config.dai
        self.dai_adapter = config.dai_join
        self.mkr = config.mkr
        self.collaterals = config.collaterals
        self.spotter = config.spotter
        self.ds_chief = config.ds_chief
        self.esm = config.esm
        self.end = config.end
        self.proxy_registry = config.proxy_registry
        self.dss_proxy_actions = config.dss_proxy_actions
        self.cdp_manager = config.cdp_manager
        self.dsr_manager = config.dsr_manager
        self.faucet = config.faucet

    @staticmethod
    def from_json(web3: Web3, conf: str):
        return DssDeployment(web3, DssDeployment.Config.from_json(web3, conf))

    def to_json(self) -> str:
        return self.config.to_json()

    @staticmethod
    def from_node(web3: Web3):
        assert isinstance(web3, Web3)

        network = DssDeployment.NETWORKS.get(web3.net.version, "testnet")

        return DssDeployment.from_network(web3=web3, network=network)

    @staticmethod
    def from_network(web3: Web3, network: str):
        assert isinstance(web3, Web3)
        assert isinstance(network, str)

        cwd = os.path.dirname(os.path.realpath(__file__))
        addresses_path = os.path.join(cwd, "../config", f"{network}-addresses.json")

        return DssDeployment.from_json(web3=web3, conf=open(addresses_path, "r").read())

    def approve_dai(self, usr: Address, **kwargs):
        """
        Allows the user to draw Dai from and repay Dai to their CDPs.

        Args
            usr: Recipient of Dai from one or more CDPs
        """
        assert isinstance(usr, Address)

        gas_strategy = kwargs['gas_strategy'] if 'gas_strategy' in kwargs else DefaultGasPrice()
        self.dai_adapter.approve(approval_function=hope_directly(from_address=usr, gas_strategy=gas_strategy),
                                 source=self.vat.address)
        self.dai.approve(self.dai_adapter.address).transact(from_address=usr, gas_strategy=gas_strategy)

    def active_auctions(self) -> dict:
        flips = {}
        clips = {}
        for collateral in self.collaterals.values():
            # Each collateral has it's own liquidation contract; add auctions from each.
            if collateral.flipper:
                flips[collateral.ilk.name] = collateral.flipper.active_auctions()
            elif collateral.clipper:
                clips[collateral.ilk.name] = collateral.clipper.active_auctions()

        return {
            "flips": flips,
            "clips": clips,
            "flaps": self.flapper.active_auctions(),
            "flops": self.flopper.active_auctions()
        }

    def __repr__(self):
        return f'DssDeployment({self.config.to_json()})'
