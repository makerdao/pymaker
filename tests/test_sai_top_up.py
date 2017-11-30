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

import pytest

from keeper import Address
from pymaker.feed import DSValue
from pymaker.numeric import Ray, Wad
from keeper.sai_top_up import SaiTopUp
from pymaker.deployment import Deployment
from tests.helper import args, captured_output


class TestSaiTopUpArguments:
    def test_should_not_start_without_eth_from_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiTopUp(args=args(f""),
                         web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --eth-from" in err.getvalue()

    def test_should_not_start_without_min_margin_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiTopUp(args=args(f"--eth-from {deployment.web3.eth.defaultAccount}"),
                         web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --min-margin" in err.getvalue()

    def test_should_not_start_without_top_up_margin_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiTopUp(args=args(f"--eth-from {deployment.web3.eth.defaultAccount} --min-margin 0.2"),
                         web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --top-up-margin" in err.getvalue()


class TestSaiTopUpBehaviour:
    @staticmethod
    def set_price(deployment: Deployment, new_price):
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(new_price).value).transact()

    def open_cdp(self, deployment: Deployment, eth_amount, sai_amount):
        # given
        deployment.tub.cuff(Ray.from_number(2.0)).transact()
        deployment.tub.cork(Wad.from_number(100000000)).transact()

        # and
        self.set_price(deployment, 500)

        # and
        deployment.tub.open().transact()
        deployment.tub.join(Wad.from_number(eth_amount)).transact()
        deployment.tub.lock(1, Wad.from_number(eth_amount)).transact()
        deployment.tub.draw(1, Wad.from_number(sai_amount)).transact()

        # and
        assert deployment.tub.ink(1) == Wad.from_number(eth_amount)
        assert deployment.tub.tab(1) == Wad.from_number(sai_amount)

    @staticmethod
    def sai_balance(deployment: Deployment, balance):
        if deployment.sai.balance_of(deployment.our_address) < Wad.from_number(balance):
            deployment.sai.mint(Wad.from_number(balance) - deployment.sai.balance_of(deployment.our_address)).transact()
        else:
            deployment.sai.transfer(Address('0x0000000000111111111100000000001111111111'),
                                    deployment.sai.balance_of(deployment.our_address) - Wad.from_number(balance)).transact()

    def test_should_top_up_if_collateralization_too_low_and_sai_below_max(self, deployment: Deployment):
        # given
        self.open_cdp(deployment, eth_amount=40, sai_amount=5000)
        self.sai_balance(deployment, balance=2500)

        # and
        keeper = SaiTopUp(args=args(f"--eth-from {deployment.web3.eth.defaultAccount} --min-margin 0.2 --top-up-margin 0.45 --max-sai 3000 --avg-sai 2000"),
                          web3=deployment.web3, config=deployment.get_config())
        keeper.approve()

        # when
        self.set_price(deployment, 276)
        # and
        keeper.check_all_cups()
        # then
        assert deployment.tub.ink(1) == Wad.from_number(40)
        assert deployment.tub.tab(1) == Wad.from_number(5000)

        # when
        self.set_price(deployment, 274)
        # and
        keeper.check_all_cups()
        # then
        assert deployment.tub.ink(1) == Wad(44708029197080290000)
        assert deployment.tub.tab(1) == Wad.from_number(5000)

    def test_should_wipe_if_collateralization_too_low_and_sai_above_max(self, deployment: Deployment):
        # given
        self.open_cdp(deployment, eth_amount=40, sai_amount=5000)
        self.sai_balance(deployment, balance=3500)

        # and
        keeper = SaiTopUp(args=args(f"--eth-from {deployment.web3.eth.defaultAccount} --min-margin 0.2 --top-up-margin 0.45 --max-sai 3000 --avg-sai 2000"),
                          web3=deployment.web3, config=deployment.get_config())
        keeper.approve()

        # when
        self.set_price(deployment, 276)
        # and
        keeper.check_all_cups()
        # then
        assert deployment.tub.ink(1) == Wad.from_number(40)
        assert deployment.tub.tab(1) == Wad.from_number(5000)
        assert deployment.sai.balance_of(deployment.our_address) == Wad.from_number(3500)

        # when
        self.set_price(deployment, 274)
        # and
        keeper.check_all_cups()
        # then
        assert deployment.tub.ink(1) == Wad.from_number(40)
        assert deployment.tub.tab(1) == Wad.from_number(3500)
        assert deployment.sai.balance_of(deployment.our_address) == Wad.from_number(2000)

    def test_should_both_wipe_and_top_up_if_collateralization_too(self, deployment: Deployment):
        # given
        self.open_cdp(deployment, eth_amount=40, sai_amount=5000)
        self.sai_balance(deployment, balance=3500)

        # and
        keeper = SaiTopUp(args=args(f"--eth-from {deployment.web3.eth.defaultAccount} --min-margin 0.2 --top-up-margin 0.45 --max-sai 3000 --avg-sai 2000"),
                          web3=deployment.web3, config=deployment.get_config())
        keeper.approve()

        # when
        self.set_price(deployment, 276)
        # and
        keeper.check_all_cups()
        # then
        assert deployment.tub.ink(1) == Wad.from_number(40)
        assert deployment.tub.tab(1) == Wad.from_number(5000)
        assert deployment.sai.balance_of(deployment.our_address) == Wad.from_number(3500)

        # when
        self.set_price(deployment, 120)
        # and
        keeper.check_all_cups()
        # then
        assert deployment.tub.ink(1) == Wad(71458333333333333000)
        assert deployment.tub.tab(1) == Wad.from_number(3500)
        assert deployment.sai.balance_of(deployment.our_address) == Wad.from_number(2000)
