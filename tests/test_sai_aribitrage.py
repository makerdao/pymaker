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
from keeper.sai_arbitrage import SaiArbitrage
from pymaker.approval import directly
from pymaker.deployment import Deployment
from pymaker.feed import DSValue
from pymaker.transactional import TxManager
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
        keeper = SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address} --base-token SAI"
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
        keeper = SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address} --base-token WETH"
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
        keeper = SaiArbitrage(args=args(f"--eth-from {deployment.our_address.address} --base-token WETH"
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
