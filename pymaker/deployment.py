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
from typing import Optional, List

import pkg_resources
from pymaker.auctions import Flapper, Flopper, Flipper
from web3 import Web3, HTTPProvider

from pymaker import Address
from pymaker.approval import directly
from pymaker.auth import DSGuard
from pymaker.etherdelta import EtherDelta
from pymaker.dss import Vat, Spotter, Vow, Drip, Pit, Cat, Collateral, DaiAdapter, DaiVat, Ilk, GemAdapter, GemVat
from pymaker.feed import DSValue
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
    """Represents a test deployment of the entire Maker smart contract ecosystem.

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
    """Represents a Dai Stablecoin System deployment.

    Static method `from_json()` should be used to instantiate all the objet of
    a deployment from a json description of all the system addresses.
    """

    class Config:
        def __init__(self, mom: DSGuard, vat: Vat, vow: Vow, drip: Drip, pit: Pit, cat: Cat, flap: Flapper,
                     flop: Flopper, dai: DSToken, dai_adapter: DaiAdapter, dai_move: DaiVat, mkr: DSToken,
                     collaterals: Optional[List[Collateral]] = None):
            self.mom = mom
            self.vat = vat
            self.vow = vow
            self.drip = drip
            self.pit = pit
            self.cat = cat
            self.flap = flap
            self.flop = flop
            self.dai = dai
            self.dai_adapter = dai_adapter
            self.dai_move = dai_move
            self.mkr = mkr
            self.collaterals = collaterals or []

        @staticmethod
        def from_json(web3: Web3, conf: str):
            conf = json.loads(conf)
            mom = DSGuard(web3, Address(conf['MCD_MOM']))
            vat = Vat(web3, Address(conf['MCD_VAT']))
            vow = Vow(web3, Address(conf['MCD_VOW']))
            drip = Drip(web3, Address(conf['MCD_DRIP']))
            pit = Pit(web3, Address(conf['MCD_PIT']))
            cat = Cat(web3, Address(conf['MCD_CAT']))
            flap = Flapper(web3, Address(conf['MCD_FLAP']))
            flop = Flopper(web3, Address(conf['MCD_FLOP']))
            dai = DSToken(web3, Address(conf['MCD_DAI']))
            dai_adapter = DaiAdapter(web3, Address(conf['MCD_JOIN_DAI']))
            dai_move = DaiVat(web3, Address(conf['MCD_MOVE_DAI']))
            mkr = DSToken(web3, Address(conf['MCD_GOV']))
            collaterals = []
            for name in conf['COLLATERALS']:
                collateral = Collateral(Ilk(name))
                collateral.gem = DSToken(web3, Address(conf[name]))
                collateral.adapter = GemAdapter(web3, Address(conf[f'MCD_JOIN_{name}']))
                collateral.mover = GemVat(web3, Address(conf[f'MCD_MOVE_{name}']))
                collateral.flipper = Flipper(web3, Address(conf[f'MCD_FLIP_{name}']))
                collateral.pip = DSValue(web3, Address(conf[f'PIP_{name}']))
                collateral.spotter = Spotter(web3, Address(conf[f'MCD_SPOT_{name}']))
                collaterals.append(collateral)
            return DssDeployment.Config(mom, vat, vow, drip, pit, cat, flap, flop, dai, dai_adapter, dai_move, mkr,
                                        collaterals)

        def to_dict(self) -> dict:
            conf_dict = {
                'MCD_MOM': self.mom.address.address,
                'MCD_VAT': self.vat.address.address,
                'MCD_VOW': self.vow.address.address,
                'MCD_DRIP': self.drip.address.address,
                'MCD_PIT': self.pit.address.address,
                'MCD_CAT': self.cat.address.address,
                'MCD_FLAP': self.flap.address.address,
                'MCD_FLOP': self.flop.address.address,
                'MCD_DAI': self.dai.address.address,
                'MCD_JOIN_DAI': self.dai_adapter.address.address,
                'MCD_MOVE_DAI': self.dai_move.address.address,
                'MCD_GOV': self.mkr.address.address,
                'COLLATERALS': []
            }

            for collateral in self.collaterals:
                name = collateral.ilk.name
                conf_dict['COLLATERALS'].append(name)
                conf_dict[name] = collateral.gem.address.address
                conf_dict[f'MCD_JOIN_{name}'] = collateral.adapter.address.address
                conf_dict[f'MCD_MOVE_{name}'] = collateral.mover.address.address
                conf_dict[f'MCD_FLIP_{name}'] = collateral.flipper.address.address
                conf_dict[f'MCD_SPOT_{name}'] = collateral.spotter.address.address
                conf_dict[f'PIP_{name}'] = collateral.pip.address.address

            return conf_dict

        def to_json(self) -> str:
            return json.dumps(self.to_dict())

    def __init__(self, web3: Web3, config: Config):
        assert isinstance(web3, Web3)
        assert isinstance(config, DssDeployment.Config)

        self.web3 = web3
        self.config = config
        self.mom = config.mom
        self.vat = config.vat
        self.vow = config.vow
        self.drip = config.drip
        self.pit = config.pit
        self.cat = config.cat
        self.flap = config.flap
        self.flop = config.flop
        self.dai = config.dai
        self.dai_adapter = config.dai_adapter
        self.dai_move = config.dai_move
        self.mkr = config.mkr
        self.collaterals = config.collaterals

    @staticmethod
    def from_json(web3: Web3, conf: str):
        return DssDeployment(web3, DssDeployment.Config.from_json(web3, conf))

    @staticmethod
    def deploy(web3: Web3, debt_ceiling: Wad):
        assert isinstance(web3, Web3)

        vat = Vat.deploy(web3=web3)

        pit = Pit.deploy(web3=web3, vat=vat.address)
        assert pit.file_global_line(debt_ceiling).transact()  # Global debt Ceiling
        assert vat.rely(pit.address).transact()

        dai = DSToken.deploy(web3=web3, symbol='DAI')
        dai_adapter = DaiAdapter.deploy(web3=web3, vat=vat.address, dai=dai.address)
        dai_move = DaiVat.deploy(web3=web3, vat=vat.address)
        assert vat.rely(dai_adapter.address).transact()
        assert vat.rely(dai_move.address).transact()

        # TODO: use a DSProxy
        mom = DSGuard.deploy(web3)
        assert mom.permit(DSGuard.ANY, DSGuard.ANY, DSGuard.ANY).transact()
        assert dai.set_authority(mom.address).transact()

        mkr = DSToken.deploy(web3=web3, symbol='MKR')

        vow = Vow.deploy(web3=web3)
        drip = Drip.deploy(web3=web3, vat=vat.address)
        flap = Flapper.deploy(web3=web3, dai=dai_move.address, gem=mkr.address)

        assert pit.file_drip(drip).transact()
        assert vow.file_vat(vat).transact()
        assert vow.file_flap(flap).transact()
        assert vow.file_bump(Wad.from_number(1000)).transact()
        assert vow.file_sump(Wad.from_number(10)).transact()
        assert drip.file_vow(vow).transact()

        assert vat.rely(vow.address).transact()
        assert vat.rely(drip.address).transact()
        assert vat.rely(flap.address).transact()

        cat = Cat.deploy(web3=web3, vat=vat.address)
        assert cat.file_vow(vow).transact()
        assert cat.file_pit(pit).transact()

        flop = Flopper.deploy(web3=web3, dai=dai_move.address, gem=mkr.address)

        assert vow.file_flop(flop).transact()

        assert vat.rely(cat.address).transact()
        assert vat.rely(flop.address).transact()
        assert vow.rely(cat.address).transact()
        assert flop.rely(vow.address).transact()

        config = DssDeployment.Config(mom, vat, vow, drip, pit, cat, flap, flop, dai, dai_adapter, dai_move, mkr)
        deployment = DssDeployment(web3, config)

        collateral = Collateral.deploy(web3=web3, name='WETH', vat=vat)
        deployment.deploy_collateral(collateral,
                                     debt_ceiling=Wad.from_number(100000),
                                     penalty=Ray.from_number(1),
                                     flop_lot=Wad.from_number(10000),
                                     ratio=Ray.from_number(1.5),
                                     initial_price=Wad.from_number(219))

        return deployment

    def deploy_collateral(self, collateral: Collateral,
                          debt_ceiling: Wad, penalty: Ray, flop_lot: Wad, ratio: Ray, initial_price: Wad):

        collateral.pip = DSValue.deploy(web3=self.web3)
        assert collateral.pip.poke_with_int(initial_price.value).transact()  # Initial price

        collateral.flipper = Flipper.deploy(web3=self.web3, dai=self.dai_move.address, gem=collateral.mover.address)

        collateral.spotter = Spotter.deploy(web3=self.web3, pit=self.pit.address, ilk=collateral.ilk)
        collateral.spotter.file_pip(collateral.pip.address).transact()
        collateral.spotter.file_mat(ratio).transact()  # Liquidation ratio

        assert collateral.gem.approve(collateral.adapter.address).transact()

        assert self.cat.file_flip(collateral.ilk, collateral.flipper).transact()
        assert self.cat.file_lump(collateral.ilk, flop_lot).transact()  # Liquidation Quantity
        assert self.cat.file_chop(collateral.ilk, penalty).transact()  # Liquidation Penalty
        assert self.vat.init(collateral.ilk).transact()
        assert self.drip.init(collateral.ilk).transact()

        assert self.vat.rely(collateral.flipper.address).transact()
        assert self.vat.rely(collateral.adapter.address).transact()
        assert self.vat.rely(collateral.mover.address).transact()
        assert self.pit.rely(collateral.spotter.address).transact()

        assert self.pit.file_line(collateral.ilk, debt_ceiling).transact()  # Collateral debt Ceiling
        assert collateral.spotter.poke().transact()

        self.collaterals.append(collateral)

    def __repr__(self):
        return f'DssDeployment({self.config.to_json()})'
