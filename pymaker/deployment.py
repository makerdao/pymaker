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
import re
from typing import Optional, List

import pkg_resources
from pymaker.auctions import Flapper, Flopper, Flipper
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.approval import directly
from pymaker.auth import DSGuard
from pymaker.etherdelta import EtherDelta
from pymaker.dss import Vat, Spotter, Vow, Jug, Cat, Collateral, DaiJoin, Ilk, GemAdapter
from pymaker.feed import DSValue
from pymaker.governance import DSPause
from pymaker.numeric import Wad, Ray
from pymaker.oasis import MatchingMarket
from pymaker.sai import Tub, Tap, Top, Vox
from pymaker.token import DSToken
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
        def __init__(self, pause: DSPause, vat: Vat, vow: Vow, jug: Jug, cat: Cat, flap: Flapper,
                     flop: Flopper, dai: DSToken, dai_join: DaiJoin, mkr: DSToken, spotter: Spotter,
                     collaterals: Optional[List[Collateral]] = None):
            self.pause = pause
            self.vat = vat
            self.vow = vow
            self.jug = jug
            self.cat = cat
            self.flap = flap
            self.flop = flop
            self.dai = dai
            self.dai_join = dai_join
            self.mkr = mkr
            self.spotter = spotter
            self.collaterals = collaterals or []

        @staticmethod
        def from_json(web3: Web3, conf: str):
            conf = json.loads(conf)
            pause = DSPause(web3, Address(conf['MCD_PAUSE']))
            vat = Vat(web3, Address(conf['MCD_VAT']))
            vow = Vow(web3, Address(conf['MCD_VOW']))
            jug = Jug(web3, Address(conf['MCD_JUG']))
            cat = Cat(web3, Address(conf['MCD_CAT']))
            flap = Flapper(web3, Address(conf['MCD_FLAP']))
            flop = Flopper(web3, Address(conf['MCD_FLOP']))
            dai = DSToken(web3, Address(conf['MCD_DAI']))
            dai_adapter = DaiJoin(web3, Address(conf['MCD_JOIN_DAI']))
            mkr = DSToken(web3, Address(conf['MCD_GOV']))
            spotter = Spotter(web3, Address(conf['MCD_SPOT']))

            collaterals = []
            for name in DssDeployment.Config._infer_collaterals_from_addresses(conf.keys()):
                collateral = Collateral(Ilk(name[0]))
                collateral.gem = DSToken(web3, Address(conf[name[1]]))
                collateral.pip = DSValue(web3, Address(conf[f'PIP_{name[1]}']))
                collateral.adapter = GemAdapter(web3, Address(conf[f'MCD_JOIN_{name[0]}']))
                collateral.flipper = Flipper(web3, Address(conf[f'MCD_FLIP_{name[0]}']))
                collaterals.append(collateral)

            return DssDeployment.Config(pause, vat, vow, jug, cat, flap, flop,
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
                'MCD_FLAP': self.flap.address.address,
                'MCD_FLOP': self.flop.address.address,
                'MCD_DAI': self.dai.address.address,
                'MCD_JOIN_DAI': self.dai_join.address.address,
                'MCD_GOV': self.mkr.address.address,
                'MCD_SPOT': self.spotter.address.address
            }

            for collateral in self.collaterals:
                match = re.search(r'(\w+)_\w+', collateral.ilk.name)
                name = (collateral.ilk.name, match.group(1))
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
        self.flap = config.flap
        self.flop = config.flop
        self.dai = config.dai
        self.dai_adapter = config.dai_join
        self.mkr = config.mkr
        self.collaterals = config.collaterals
        self.spotter = config.spotter

    @staticmethod
    def from_json(web3: Web3, conf: str):
        return DssDeployment(web3, DssDeployment.Config.from_json(web3, conf))

    def to_json(self):
        return self.config.to_json()

    @staticmethod
    def deploy(web3: Web3):
        assert isinstance(web3, Web3)

        # deployVat
        vat = Vat.deploy(web3=web3)
        assert vat.rely(Address(web3.eth.defaultAccount)).transact(
            from_address=Address(eth_utils.to_checksum_address(web3.eth.defaultAccount)))
        spotter = Spotter.deploy(web3=web3, vat=vat.address)
        assert vat.rely(spotter.address).transact()

        # deployDai
        dai = DSToken.deploy(web3=web3, symbol='DAI')
        dai_join = DaiJoin.deploy(web3=web3, vat=vat.address, dai=dai.address)
        dai.rely(dai_join)
        assert vat.rely(dai_join.address).transact()

        mkr = DSToken.deploy(web3=web3, symbol='MKR')

        # TODO: use a DSProxy, and auth this with Cat and Vow
        pause = DSPause.deploy(web3, web3.eth.defaultAccount, Address("0x0"))

        vow = Vow.deploy(web3=web3)
        jug = Jug.deploy(web3=web3, vat=vat.address)
        flap = Flapper.deploy(web3=web3, dai=dai.address, gem=mkr.address)

        assert vow.file_vat(vat).transact()
        assert vow.file_flap(flap).transact()
        assert vow.file_bump(Wad.from_number(1000)).transact()
        assert vow.file_sump(Wad.from_number(10)).transact()
        assert jug.file_vow(vow).transact()

        assert vat.rely(vow.address).transact()
        assert vat.rely(jug.address).transact()
        assert vat.rely(flap.address).transact()

        cat = Cat.deploy(web3=web3, vat=vat.address)
        assert cat.file_vow(vow).transact()

        flop = Flopper.deploy(web3=web3, dai=dai.address, gem=mkr.address)

        assert vow.file_flop(flop).transact()

        assert vat.rely(cat.address).transact()
        assert vat.rely(flop.address).transact()
        assert vow.rely(cat.address).transact()
        assert flop.rely(vow.address).transact()

        spotter = Spotter.deploy(web3=web3, vat=vat.address)

        config = DssDeployment.Config(pause, vat, vow, jug, cat, flap, flop, dai, dai_join, mkr, spotter)
        deployment = DssDeployment(web3, config)

        collateral = Collateral.deploy(web3=web3, name='WETH', vat=vat)
        deployment.deploy_collateral(collateral, spotter,
                                     debt_ceiling=Wad.from_number(100000),
                                     penalty=Ray.from_number(1),
                                     flop_lot=Wad.from_number(10000),
                                     ratio=Ray.from_number(1.5),
                                     initial_price=Wad.from_number(219))

        return deployment

    def deploy_collateral(self, collateral: Collateral, spotter: Spotter,
                          debt_ceiling: Wad, penalty: Ray, flop_lot: Wad, ratio: Ray, initial_price: Wad):
        assert isinstance(collateral, Collateral)
        assert collateral.ilk.name is not None
        assert self.vat.address is not None
        assert self.cat.address is not None

        collateral.pip = DSValue.deploy(web3=self.web3)
        assert collateral.pip.address is not None
        assert collateral.pip.poke_with_int(initial_price.value).transact()  # Initial price
        collateral.flipper = Flipper.deploy(web3=self.web3, vat=self.vat.address, ilk=collateral.ilk.toBytes())

        assert self.vat.init(collateral.ilk).transact()
        assert self.vat.file_line(collateral.ilk, debt_ceiling)

        assert collateral.gem.approve(collateral.adapter.address).transact()

        # FIXME: Flipper.flips may not be populating with all the required fields.
        assert self.cat.file_flip(collateral.ilk, collateral.flipper).transact()
        assert self.cat.file_lump(collateral.ilk, flop_lot).transact()  # Liquidation Quantity
        assert self.cat.file_chop(collateral.ilk, penalty).transact()  # Liquidation Penalty
        assert self.jug.init(collateral.ilk).transact()

        assert self.vat.rely(collateral.flipper.address).transact()
        assert self.vat.rely(collateral.adapter.address).transact()

        spotter.file_pip(collateral.ilk, collateral.pip.address).transact()
        spotter.file_mat(collateral.ilk, ratio).transact()  # Liquidation ratio
        # FIXME: Figure out why this fails with {'code': -32016, 'message': 'The execution failed due to an exception.'}
        assert spotter.poke(collateral.ilk).transact()

        self.collaterals.append(collateral)

    def __repr__(self):
        return f'DssDeployment({self.config.to_json()})'
