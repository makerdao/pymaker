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
