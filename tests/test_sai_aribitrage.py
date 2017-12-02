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

from keeper import Wad
from pymaker.approval import directly
from pymaker.feed import DSValue
from keeper.sai_arbitrage import SaiArbitrage
from pymaker.deployment import Deployment
from tests.helper import args, captured_output


class TestSaiArbitrage:
    def test_should_not_start_without_eth_from_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiArbitrage(args=args(f""),
                             web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --eth-from" in err.getvalue()

    def test_should_not_start_without_base_token_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address}"),
                             web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --base-token" in err.getvalue()

    def test_should_not_start_without_min_profit_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address} --base-token SAI"),
                             web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --min-profit" in err.getvalue()

    def test_should_not_start_without_max_engagement_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address} --base-token SAI"
                                       f" --min-profit 1.0"),
                             web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --max-engagement" in err.getvalue()

    def test_should_not_start_if_base_token_is_invalid(self, deployment: Deployment):
        # expect
        with pytest.raises(Exception):
            SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address} --base-token SAJ"
                                   f" --min-profit 1.0 --max-engagement 1000.0"),
                         web3=deployment.web3, config=deployment.get_config())

    def test_should_not_do_anything_if_no_arbitrage_opportunities(self, deployment: Deployment):
        # given
        keeper = SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address} --base-token SAI"
                                        f" --min-profit 1.0 --max-engagement 1000.0"),
                              web3=deployment.web3, config=deployment.get_config())

        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        deployment.tap.jump(Wad.from_number(1.05)).transact()

        # when
        keeper.approve()
        keeper.process_block()

        # then
        # (nothing happens)

    def test_should_identify_multi_step_arbitrage_on_oasis(self, deployment: Deployment):
        # given
        keeper = SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address} --base-token SAI"
                                        f" --min-profit 13.0 --max-engagement 100.0"),
                              web3=deployment.web3, config=deployment.get_config())

        # and
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        deployment.tub.jar_jump(Wad.from_number(1.05)).transact()
        deployment.tub.join(Wad.from_number(1000)).transact()
        deployment.tap.jump(Wad.from_number(1.05)).transact()

        # and
        deployment.sai.mint(Wad.from_number(1000)).transact()

        # and
        deployment.otc.approve([deployment.gem, deployment.sai, deployment.skr], directly())
        deployment.otc.add_token_pair_whitelist(deployment.sai.address, deployment.skr.address).transact()
        deployment.otc.add_token_pair_whitelist(deployment.skr.address, deployment.gem.address).transact()
        deployment.otc.add_token_pair_whitelist(deployment.gem.address, deployment.sai.address).transact()
        deployment.otc.make(deployment.skr.address, Wad.from_number(105), deployment.sai.address, Wad.from_number(100)).transact()
        deployment.otc.make(deployment.gem.address, Wad.from_number(110), deployment.skr.address, Wad.from_number(105)).transact()
        deployment.otc.make(deployment.sai.address, Wad.from_number(115), deployment.gem.address, Wad.from_number(110)).transact()
        assert len(deployment.otc.get_orders()) == 3

        # when
        keeper.approve()
        keeper.process_block()

        # then
        assert len(deployment.otc.get_orders()) == 0

    def test_should_obey_max_engagement(self, deployment: Deployment):
        # given
        keeper = SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address} --base-token SAI"
                                        f" --min-profit 1.0 --max-engagement 90.0"),
                              web3=deployment.web3, config=deployment.get_config())

        # and
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        deployment.tub.jar_jump(Wad.from_number(1.05)).transact()
        deployment.tub.join(Wad.from_number(1000)).transact()
        deployment.tap.jump(Wad.from_number(1.05)).transact()

        # and
        deployment.sai.mint(Wad.from_number(1000)).transact()

        # and
        deployment.otc.approve([deployment.gem, deployment.sai, deployment.skr], directly())
        deployment.otc.add_token_pair_whitelist(deployment.sai.address, deployment.skr.address).transact()
        deployment.otc.add_token_pair_whitelist(deployment.skr.address, deployment.gem.address).transact()
        deployment.otc.add_token_pair_whitelist(deployment.gem.address, deployment.sai.address).transact()
        deployment.otc.make(deployment.skr.address, Wad.from_number(105), deployment.sai.address, Wad.from_number(100)).transact()
        deployment.otc.make(deployment.gem.address, Wad.from_number(110), deployment.skr.address, Wad.from_number(105)).transact()
        deployment.otc.make(deployment.sai.address, Wad.from_number(115), deployment.gem.address, Wad.from_number(110)).transact()
        assert len(deployment.otc.get_orders()) == 3

        # when
        keeper.approve()
        keeper.process_block()

        # then
        assert len(deployment.otc.get_orders()) == 3
        assert deployment.otc.get_orders()[0].buy_how_much == Wad.from_number(10)

    def test_should_obey_min_profit(self, deployment: Deployment):
        # given
        keeper = SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address} --base-token SAI"
                                        f" --min-profit 16.0 --max-engagement 1000.0"),
                              web3=deployment.web3, config=deployment.get_config())

        # and
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        deployment.tub.jar_jump(Wad.from_number(1.05)).transact()
        deployment.tub.join(Wad.from_number(1000)).transact()
        deployment.tap.jump(Wad.from_number(1.05)).transact()

        # and
        deployment.sai.mint(Wad.from_number(1000)).transact()

        # and
        deployment.otc.approve([deployment.gem, deployment.sai, deployment.skr], directly())
        deployment.otc.add_token_pair_whitelist(deployment.sai.address, deployment.skr.address).transact()
        deployment.otc.add_token_pair_whitelist(deployment.skr.address, deployment.gem.address).transact()
        deployment.otc.add_token_pair_whitelist(deployment.gem.address, deployment.sai.address).transact()
        deployment.otc.make(deployment.skr.address, Wad.from_number(105), deployment.sai.address, Wad.from_number(100)).transact()
        deployment.otc.make(deployment.gem.address, Wad.from_number(110), deployment.skr.address, Wad.from_number(105)).transact()
        deployment.otc.make(deployment.sai.address, Wad.from_number(115), deployment.gem.address, Wad.from_number(110)).transact()
        assert len(deployment.otc.get_orders()) == 3

        # when
        keeper.approve()
        keeper.process_block()

        # then
        assert len(deployment.otc.get_orders()) == 3
        assert deployment.otc.get_orders()[0].buy_how_much == Wad.from_number(100)
        assert deployment.otc.get_orders()[1].buy_how_much == Wad.from_number(105)
        assert deployment.otc.get_orders()[2].buy_how_much == Wad.from_number(110)
