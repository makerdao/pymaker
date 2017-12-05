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

from arbitrage_keeper.arbitrage_keeper import ArbitrageKeeper
from pymaker.approval import directly
from pymaker.deployment import Deployment
from pymaker.feed import DSValue
from pymaker.numeric import Wad, Ray
from pymaker.transactional import TxManager
from tests.helper import args, captured_output


class TestArbitrageKeeper:
    def test_should_not_start_without_eth_from_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                ArbitrageKeeper(args=args(f""),
                                web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --eth-from" in err.getvalue()

    def test_should_not_start_without_tub_address_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"),
                                web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --tub-address" in err.getvalue()

    def test_should_not_start_without_tap_address_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                       f" --tub-address {deployment.tub.address}"),
                                web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --tap-address" in err.getvalue()

    def test_should_not_start_without_oasis_address_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                       f" --tub-address {deployment.tub.address}"
                                       f" --tap-address {deployment.tap.address}"),
                                web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --oasis-address" in err.getvalue()

    def test_should_not_start_without_base_token_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                       f" --tub-address {deployment.tub.address}"
                                       f" --tap-address {deployment.tap.address}"
                                       f" --oasis-address {deployment.otc.address}"),
                                web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --base-token" in err.getvalue()

    def test_should_not_start_without_min_profit_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                       f" --tub-address {deployment.tub.address}"
                                       f" --tap-address {deployment.tap.address}"
                                       f" --oasis-address {deployment.otc.address}"
                                       f" --base-token {deployment.sai.address}"),
                                web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --min-profit" in err.getvalue()

    def test_should_not_start_without_max_engagement_argument(self, deployment: Deployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                       f" --tub-address {deployment.tub.address}"
                                       f" --tap-address {deployment.tap.address}"
                                       f" --oasis-address {deployment.otc.address}"
                                       f" --base-token {deployment.sai.address}"
                                       f" --min-profit 1.0"),
                                web3=deployment.web3, config=deployment.get_config())

        # then
        assert "error: the following arguments are required: --max-engagement" in err.getvalue()

    def test_should_not_start_if_base_token_is_invalid(self, deployment: Deployment):
        # expect
        with pytest.raises(Exception):
            ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                   f" --tub-address {deployment.tub.address}"
                                   f" --tap-address {deployment.tap.address}"
                                   f" --oasis-address {deployment.otc.address}"
                                   f" --base-token 0x1121211212112121121211212112121121211212"
                                   f" --min-profit 1.0 --max-engagement 1000.0"),
                            web3=deployment.web3, config=deployment.get_config())

    def test_should_not_do_anything_if_no_arbitrage_opportunities(self, deployment: Deployment):
        # given
        keeper = ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                        f" --tub-address {deployment.tub.address}"
                                        f" --tap-address {deployment.tap.address}"
                                        f" --oasis-address {deployment.otc.address}"
                                        f" --base-token {deployment.sai.address}"
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
        keeper = ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                        f" --tub-address {deployment.tub.address}"
                                        f" --tap-address {deployment.tap.address}"
                                        f" --oasis-address {deployment.otc.address}"
                                        f" --base-token {deployment.sai.address}"
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
        block_number_before = deployment.web3.eth.blockNumber
        keeper.process_block()
        block_number_after = deployment.web3.eth.blockNumber

        # then
        assert len(deployment.otc.get_orders()) == 0

        # and
        # [keeper used three transactions, as TxManager is not configured]
        assert (block_number_after - block_number_before) == 3

    def test_should_execute_arbitrage_in_one_transaction_if_tx_manager_configured(self, deployment: Deployment):
        # given
        tx_manager = TxManager.deploy(deployment.web3)

        # and
        keeper = ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                        f" --tub-address {deployment.tub.address}"
                                        f" --tap-address {deployment.tap.address}"
                                        f" --oasis-address {deployment.otc.address}"
                                        f" --base-token {deployment.sai.address}"
                                        f" --min-profit 13.0 --max-engagement 100.0"
                                        f" --tx-manager {tx_manager.address}"),
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
        block_number_before = deployment.web3.eth.blockNumber
        keeper.process_block()
        block_number_after = deployment.web3.eth.blockNumber

        # then
        assert len(deployment.otc.get_orders()) == 0

        # and
        # [keeper used only one transaction, as TxManager is configured]
        assert (block_number_after - block_number_before) == 1

    def test_should_identify_arbitrage_against_oasis_and_join(self, deployment: Deployment):
        # given
        keeper = ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                        f" --tub-address {deployment.tub.address}"
                                        f" --tap-address {deployment.tap.address}"
                                        f" --oasis-address {deployment.otc.address}"
                                        f" --base-token {deployment.gem.address}"
                                        f" --min-profit 5.0 --max-engagement 100.0"),
                                 web3=deployment.web3, config=deployment.get_config())

        # and
        # [a price is set, so the arbitrage keeper knows prices of `boom` and `bust`]
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()

        # and
        # [we have 100 WETH]
        deployment.gem.mint(Wad.from_number(100)).transact()

        # and
        # [somebody else placed an order on OASIS offering 110 WETH for 100 SKR]
        deployment.tub.join(Wad.from_number(110)).transact()
        deployment.otc.approve([deployment.gem, deployment.skr], directly())
        deployment.otc.add_token_pair_whitelist(deployment.skr.address, deployment.gem.address).transact()
        deployment.otc.make(deployment.gem.address, Wad.from_number(110), deployment.skr.address, Wad.from_number(100)).transact()
        assert deployment.skr.total_supply() == Wad.from_number(110)
        assert len(deployment.otc.get_orders()) == 1

        # when
        keeper.approve()
        keeper.process_block()

        # then
        # [the order on Oasis has been taken by the keeper]
        assert len(deployment.otc.get_orders()) == 0

        # and
        # [the total supply of SKR has increased, so we know the keeper did call join('100.0')]
        assert deployment.skr.total_supply() == Wad.from_number(210)

    def test_should_identify_arbitrage_against_oasis_and_exit(self, deployment: Deployment):
        # given
        keeper = ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                        f" --tub-address {deployment.tub.address}"
                                        f" --tap-address {deployment.tap.address}"
                                        f" --oasis-address {deployment.otc.address}"
                                        f" --base-token {deployment.gem.address}"
                                        f" --min-profit 5.0 --max-engagement 100.0"),
                                 web3=deployment.web3, config=deployment.get_config())

        # and
        # [a price is set, so the arbitrage keeper knows prices of `boom` and `bust`]
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()

        # and
        # [we have 100 WETH]
        deployment.gem.mint(Wad.from_number(100)).transact()

        # and
        # [somebody else placed an order on OASIS offering 110 SKR for 100 WETH]
        deployment.gem.mint(Wad.from_number(110)).transact()
        deployment.tub.join(Wad.from_number(110)).transact()
        deployment.otc.approve([deployment.gem, deployment.skr], directly())
        deployment.otc.add_token_pair_whitelist(deployment.skr.address, deployment.gem.address).transact()
        deployment.otc.make(deployment.skr.address, Wad.from_number(110), deployment.gem.address, Wad.from_number(100)).transact()
        assert deployment.skr.total_supply() == Wad.from_number(110)
        assert len(deployment.otc.get_orders()) == 1

        # when
        keeper.approve()
        keeper.process_block()

        # then
        # [the order on Oasis has been taken by the keeper]
        assert len(deployment.otc.get_orders()) == 0

        # and
        # [the total supply of SKR has decreased, so we know the keeper did call exit('110.0')]
        assert deployment.skr.total_supply() == Wad.from_number(0)

    def test_should_identify_arbitrage_against_oasis_and_bust(self, deployment: Deployment):
        # given
        keeper = ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                        f" --tub-address {deployment.tub.address}"
                                        f" --tap-address {deployment.tap.address}"
                                        f" --oasis-address {deployment.otc.address}"
                                        f" --base-token {deployment.sai.address}"
                                        f" --min-profit 950.0 --max-engagement 14250.0"),
                                 web3=deployment.web3, config=deployment.get_config())

        # and
        # [we generate some bad debt available for `bust`]
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        deployment.tub.cork(Wad.from_number(1000000)).transact()
        deployment.tub.cuff(Ray.from_number(2.0)).transact()
        deployment.tub.chop(Ray.from_number(2.0)).transact()
        deployment.gem.mint(Wad.from_number(100)).transact()
        deployment.tub.join(Wad.from_number(100)).transact()
        deployment.tub.open().transact()
        deployment.tub.lock(1, Wad.from_number(100)).transact()
        deployment.tub.draw(1, Wad.from_number(25000)).transact()
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(400).value).transact()
        deployment.tub.bite(1).transact()
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        assert deployment.tap.woe() == Wad.from_number(25000)
        assert deployment.tap.fog() == Wad.from_number(100)

        # and
        # [we add a boom/bust spread to make calculations a bit more difficult]
        deployment.tap.jump(Wad.from_number(0.95)).transact()
        assert deployment.tap.ask() == Wad.from_number(475.0)
        assert deployment.tap.bid() == Wad.from_number(525.0)

        # and
        # [we have some SKR to cover rounding errors]
        deployment.skr.mint(Wad.from_number(0.000000000000000001)).transact()

        # and
        # [we should now have 30 SKR available for 14250 SAI on `bust`]
        # [now lets pretend somebody else placed an order on OASIS offering 15250 SAI for these 30 SKR]
        # [this will be an arbitrage opportunity which can make the bot earn 1000 SAI]
        deployment.sai.mint(Wad.from_number(15250)).transact()
        deployment.otc.approve([deployment.sai, deployment.skr], directly())
        deployment.otc.add_token_pair_whitelist(deployment.skr.address, deployment.sai.address).transact()
        deployment.otc.make(deployment.sai.address, Wad.from_number(15250), deployment.skr.address, Wad.from_number(30)).transact()
        assert len(deployment.otc.get_orders()) == 1

        # when
        keeper.approve()
        keeper.process_block()

        # then
        # [the order on Oasis has been taken by the keeper]
        assert len(deployment.otc.get_orders()) == 0

        # and
        # [the amount of bad debt has decreased, so we know the keeper did call bust('14250.0')]
        # [the inequality below is to cater for rounding errors]
        assert deployment.tap.woe() < Wad.from_number(10800.0)

    def test_should_obey_max_engagement(self, deployment: Deployment):
        # given
        keeper = ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                        f" --tub-address {deployment.tub.address}"
                                        f" --tap-address {deployment.tap.address}"
                                        f" --oasis-address {deployment.otc.address}"
                                        f" --base-token {deployment.sai.address}"
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
        keeper = ArbitrageKeeper(args=args(f"--eth-from {deployment.our_address.address}"
                                        f" --tub-address {deployment.tub.address}"
                                        f" --tap-address {deployment.tap.address}"
                                        f" --oasis-address {deployment.otc.address}"
                                        f" --base-token {deployment.sai.address}"
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
