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
from keeper.api.feed import DSValue
from keeper.api.numeric import Ray, Wad
from keeper.sai_top_up import SaiTopUp
from tests.conftest import SaiDeployment
from tests.helper import args, captured_output


class TestSaiTopUpArguments:
    def test_should_not_start_without_eth_from_argument(self, sai: SaiDeployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiTopUp(args=args(f""),
                         web3=sai.web3, config=sai.get_config())

        # then
        assert "error: the following arguments are required: --eth-from" in err.getvalue()

    def test_should_not_start_without_min_margin_argument(self, sai: SaiDeployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiTopUp(args=args(f"--eth-from {sai.web3.eth.defaultAccount}"),
                         web3=sai.web3, config=sai.get_config())

        # then
        assert "error: the following arguments are required: --min-margin" in err.getvalue()

    def test_should_not_start_without_top_up_margin_argument(self, sai: SaiDeployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiTopUp(args=args(f"--eth-from {sai.web3.eth.defaultAccount} --min-margin 0.2"),
                         web3=sai.web3, config=sai.get_config())

        # then
        assert "error: the following arguments are required: --top-up-margin" in err.getvalue()


class TestSaiTopUpBehaviour:
    @staticmethod
    def set_price(sai: SaiDeployment, new_price):
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(new_price).value).transact()

    def open_cdp(self, sai: SaiDeployment, eth_amount, sai_amount):
        # given
        sai.tub.cuff(Ray.from_number(2.0)).transact()
        sai.tub.cork(Wad.from_number(100000000)).transact()

        # and
        self.set_price(sai, 500)

        # and
        sai.tub.open().transact()
        sai.tub.join(Wad.from_number(eth_amount)).transact()
        sai.tub.lock(1, Wad.from_number(eth_amount)).transact()
        sai.tub.draw(1, Wad.from_number(sai_amount)).transact()

        # and
        assert sai.tub.ink(1) == Wad.from_number(eth_amount)
        assert sai.tub.tab(1) == Wad.from_number(sai_amount)

    @staticmethod
    def sai_balance(sai: SaiDeployment, balance):
        if sai.sai.balance_of(sai.our_address) < Wad.from_number(balance):
            sai.sai.mint(Wad.from_number(balance) - sai.sai.balance_of(sai.our_address)).transact()
        else:
            sai.sai.transfer(Address('0x0000000000111111111100000000001111111111'),
                                     sai.sai.balance_of(sai.our_address) - Wad.from_number(balance)).transact()

    def test_should_top_up_if_collateralization_too_low_and_sai_below_max(self, sai: SaiDeployment):
        # given
        self.open_cdp(sai, eth_amount=40, sai_amount=5000)
        self.sai_balance(sai, balance=2500)

        # and
        keeper = SaiTopUp(args=args(f"--eth-from {sai.web3.eth.defaultAccount} --min-margin 0.2 --top-up-margin 0.45 --max-sai 3000 --avg-sai 2000"),
                          web3=sai.web3, config=sai.get_config())
        keeper.approve()

        # when
        self.set_price(sai, 276)
        # and
        keeper.check_all_cups()
        # then
        assert sai.tub.ink(1) == Wad.from_number(40)
        assert sai.tub.tab(1) == Wad.from_number(5000)

        # when
        self.set_price(sai, 274)
        # and
        keeper.check_all_cups()
        # then
        assert sai.tub.ink(1) == Wad(44708029197080290000)
        assert sai.tub.tab(1) == Wad.from_number(5000)

    def test_should_wipe_if_collateralization_too_low_and_sai_above_max(self, sai: SaiDeployment):
        # given
        self.open_cdp(sai, eth_amount=40, sai_amount=5000)
        self.sai_balance(sai, balance=3500)

        # and
        keeper = SaiTopUp(args=args(f"--eth-from {sai.web3.eth.defaultAccount} --min-margin 0.2 --top-up-margin 0.45 --max-sai 3000 --avg-sai 2000"),
                          web3=sai.web3, config=sai.get_config())
        keeper.approve()

        # when
        self.set_price(sai, 276)
        # and
        keeper.check_all_cups()
        # then
        assert sai.tub.ink(1) == Wad.from_number(40)
        assert sai.tub.tab(1) == Wad.from_number(5000)
        assert sai.sai.balance_of(sai.our_address) == Wad.from_number(3500)

        # when
        self.set_price(sai, 274)
        # and
        keeper.check_all_cups()
        # then
        assert sai.tub.ink(1) == Wad.from_number(40)
        assert sai.tub.tab(1) == Wad.from_number(3500)
        assert sai.sai.balance_of(sai.our_address) == Wad.from_number(2000)

    def test_should_both_wipe_and_top_up_if_collateralization_too(self, sai: SaiDeployment):
        # given
        self.open_cdp(sai, eth_amount=40, sai_amount=5000)
        self.sai_balance(sai, balance=3500)

        # and
        keeper = SaiTopUp(args=args(f"--eth-from {sai.web3.eth.defaultAccount} --min-margin 0.2 --top-up-margin 0.45 --max-sai 3000 --avg-sai 2000"),
                          web3=sai.web3, config=sai.get_config())
        keeper.approve()

        # when
        self.set_price(sai, 276)
        # and
        keeper.check_all_cups()
        # then
        assert sai.tub.ink(1) == Wad.from_number(40)
        assert sai.tub.tab(1) == Wad.from_number(5000)
        assert sai.sai.balance_of(sai.our_address) == Wad.from_number(3500)

        # when
        self.set_price(sai, 120)
        # and
        keeper.check_all_cups()
        # then
        assert sai.tub.ink(1) == Wad(71458333333333333000)
        assert sai.tub.tab(1) == Wad.from_number(3500)
        assert sai.sai.balance_of(sai.our_address) == Wad.from_number(2000)
