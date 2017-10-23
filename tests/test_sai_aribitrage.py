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
from keeper.api.approval import directly
from keeper.api.feed import DSValue
from keeper.sai_arbitrage import SaiArbitrage
from keeper.sai_bite import SaiBite
from tests.conftest import SaiDeployment
from tests.helper import args, captured_output


class TestSaiArbitrage:
    def test_should_not_start_without_eth_from_argument(self, sai: SaiDeployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiArbitrage(args=args(f""),
                             web3=sai.web3, config=sai.get_config())

        # then
        assert "error: the following arguments are required: --eth-from" in err.getvalue()

    def test_should_not_start_without_base_token_argument(self, sai: SaiDeployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiArbitrage(args=args(f"--eth-from {sai.our_address.address}"),
                             web3=sai.web3, config=sai.get_config())

        # then
        assert "error: the following arguments are required: --base-token" in err.getvalue()

    def test_should_not_start_without_min_profit_argument(self, sai: SaiDeployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiArbitrage(args=args(f"--eth-from {sai.our_address.address} --base-token SAI"),
                             web3=sai.web3, config=sai.get_config())

        # then
        assert "error: the following arguments are required: --min-profit" in err.getvalue()

    def test_should_not_start_without_max_engagement_argument(self, sai: SaiDeployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiArbitrage(args=args(f"--eth-from {sai.our_address.address} --base-token SAI"
                                       f" --min-profit 1.0"),
                             web3=sai.web3, config=sai.get_config())

        # then
        assert "error: the following arguments are required: --max-engagement" in err.getvalue()

    def test_should_not_start_if_base_token_is_invalid(self, sai: SaiDeployment):
        # expect
        with pytest.raises(Exception):
            SaiArbitrage(args=args(f"--eth-from {sai.our_address.address} --base-token SAJ"
                                   f" --min-profit 1.0 --max-engagement 1000.0"),
                         web3=sai.web3, config=sai.get_config())

    def test_should_not_do_anything_if_no_arbitrage_opportunities(self, sai: SaiDeployment):
        # given
        keeper = SaiArbitrage(args=args(f"--eth-from {sai.our_address.address} --base-token SAI"
                                        f" --min-profit 1.0 --max-engagement 1000.0"),
                              web3=sai.web3, config=sai.get_config())

        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        sai.tap.jump(Wad.from_number(1.05)).transact()

        # when
        keeper.process_block()

        # then
        # (nothing happens)

    def test_should_identify_multi_step_arbitrage_on_oasis(self, sai: SaiDeployment):
        # given
        keeper = SaiArbitrage(args=args(f"--eth-from {sai.our_address.address} --base-token SAI"
                                        f" --min-profit 1.0 --max-engagement 100.0"),
                              web3=sai.web3, config=sai.get_config())

        # and
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        sai.tub.jar_jump(Wad.from_number(1.05)).transact()
        sai.tub.join(Wad.from_number(1000)).transact()
        sai.tap.jump(Wad.from_number(1.05)).transact()

        # and
        sai.sai.mint(Wad.from_number(1000)).transact()

        # and
        sai.otc.approve([sai.gem, sai.sai, sai.skr], directly())
        sai.otc.add_token_pair_whitelist(sai.sai.address, sai.skr.address).transact()
        sai.otc.add_token_pair_whitelist(sai.skr.address, sai.gem.address).transact()
        sai.otc.add_token_pair_whitelist(sai.gem.address, sai.sai.address).transact()
        sai.otc.make(sai.skr.address, Wad.from_number(105), sai.sai.address, Wad.from_number(100)).transact()
        sai.otc.make(sai.gem.address, Wad.from_number(110), sai.skr.address, Wad.from_number(105)).transact()
        sai.otc.make(sai.sai.address, Wad.from_number(115), sai.gem.address, Wad.from_number(110)).transact()
        assert len(sai.otc.active_offers()) == 3

        # when
        keeper.process_block()

        # then
        assert len(sai.otc.active_offers()) == 0

    def test_should_obey_max_engagement(self, sai: SaiDeployment):
        # given
        keeper = SaiArbitrage(args=args(f"--eth-from {sai.our_address.address} --base-token SAI"
                                        f" --min-profit 1.0 --max-engagement 90.0"),
                              web3=sai.web3, config=sai.get_config())

        # and
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        sai.tub.jar_jump(Wad.from_number(1.05)).transact()
        sai.tub.join(Wad.from_number(1000)).transact()
        sai.tap.jump(Wad.from_number(1.05)).transact()

        # and
        sai.sai.mint(Wad.from_number(1000)).transact()

        # and
        sai.otc.approve([sai.gem, sai.sai, sai.skr], directly())
        sai.otc.add_token_pair_whitelist(sai.sai.address, sai.skr.address).transact()
        sai.otc.add_token_pair_whitelist(sai.skr.address, sai.gem.address).transact()
        sai.otc.add_token_pair_whitelist(sai.gem.address, sai.sai.address).transact()
        sai.otc.make(sai.skr.address, Wad.from_number(105), sai.sai.address, Wad.from_number(100)).transact()
        sai.otc.make(sai.gem.address, Wad.from_number(110), sai.skr.address, Wad.from_number(105)).transact()
        sai.otc.make(sai.sai.address, Wad.from_number(115), sai.gem.address, Wad.from_number(110)).transact()
        assert len(sai.otc.active_offers()) == 3

        # when
        keeper.process_block()

        # then
        assert len(sai.otc.active_offers()) == 3
        assert sai.otc.active_offers()[0].buy_how_much == Wad.from_number(10)
