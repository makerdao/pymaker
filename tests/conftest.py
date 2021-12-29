# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2019 reverendus, EdNoepel
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
import pytest

from web3 import Web3, HTTPProvider
from web3._utils.events import AttributeDict


from pymaker import Address, web3_via_http
from pymaker.auctions import Flipper, Flapper, Flopper
from pymaker.deployment import Deployment, DssDeployment
from pymaker.dss import Vat, Vow, Cat, Dog, Jug, Pot
from pymaker.keys import register_keys


@pytest.fixture(scope='session')
def new_deployment() -> Deployment:
    return Deployment()


@pytest.fixture()
def deployment(new_deployment: Deployment) -> Deployment:
    new_deployment.reset()
    return new_deployment


@pytest.fixture(scope="session")
def web3() -> Web3:
    # for local dockerized parity testchain
    web3 = web3_via_http("http://0.0.0.0:8545")
    web3.eth.defaultAccount = "0x50FF810797f75f6bfbf2227442e0c961a8562F4C"
    register_keys(web3,
                  ["key_file=tests/config/keys/UnlimitedChain/key1.json,pass_file=/dev/null",
                   "key_file=tests/config/keys/UnlimitedChain/key2.json,pass_file=/dev/null",
                   "key_file=tests/config/keys/UnlimitedChain/key3.json,pass_file=/dev/null",
                   "key_file=tests/config/keys/UnlimitedChain/key4.json,pass_file=/dev/null",
                   "key_file=tests/config/keys/UnlimitedChain/key.json,pass_file=/dev/null"])

    # reduce logspew
    logging.getLogger("web3").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.INFO)

    assert len(web3.eth.accounts) > 3
    return web3


def patch_web3_block_data(web3, mocker, base_fee):
    # TODO: Build a new testchain with a node which provides EIP-1559 baseFee in getBlock response.
    block_data = dict(web3.eth.get_block('pending'))
    block_data['baseFeePerGas'] = base_fee
    mocker.patch.object(web3.eth, 'get_block', return_value=AttributeDict(block_data))


@pytest.fixture(scope="session")
def our_address(web3) -> Address:
    return Address(web3.eth.accounts[0])


@pytest.fixture(scope="session")
def other_address(web3) -> Address:
    return Address(web3.eth.accounts[1])


@pytest.fixture(scope="session")
def deployment_address(web3) -> Address:
    # FIXME: Unsure why it isn't added to web3.eth.accounts list
    return Address("0x00a329c0648769A73afAc7F9381E08FB43dBEA72")


@pytest.fixture(scope="session")
def mcd(web3) -> DssDeployment:
    # for local dockerized parity testchain
    deployment = DssDeployment.from_node(web3=web3)
    validate_contracts_loaded(deployment)
    initialize_collaterals(deployment)
    return deployment


def validate_contracts_loaded(deployment: DssDeployment):
    assert isinstance(deployment.vat, Vat)
    assert deployment.vat.address is not None
    assert isinstance(deployment.vow, Vow)
    assert deployment.vow.address is not None
    assert isinstance(deployment.cat, Cat)
    assert deployment.cat.address is not None
    assert isinstance(deployment.dog, Dog)
    assert deployment.dog.address is not None
    assert isinstance(deployment.jug, Jug)
    assert deployment.jug.address is not None
    assert isinstance(deployment.flapper, Flapper)
    assert deployment.flapper.address is not None
    assert isinstance(deployment.flopper, Flopper)
    assert deployment.flopper.address is not None
    assert isinstance(deployment.pot, Pot)
    assert deployment.pot.address is not None


def initialize_collaterals(deployment: DssDeployment):
    for collateral in deployment.collaterals.values():
        if collateral.clipper:
            collateral.clipper.upchost().transact(from_address=deployment_address(deployment.web3))
