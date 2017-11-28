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
    def test_should_bite_unsafe_cups_only(self, sai: SaiDeployment):
        # given
        sai.tub.cuff(Ray.from_number(2.0)).transact()

        # and
        keeper = SaiTopUp(args=args(f"--eth-from {sai.web3.eth.defaultAccount} --min-margin 0.2 --top-up-margin 0.45"),
                          web3=sai.web3, config=sai.get_config())

        # and
        sai.tub.join(Wad.from_number(10)).transact()
        sai.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # and
        sai.tub.open().transact()
        sai.tub.lock(1, Wad.from_number(4)).transact()
        sai.tub.draw(1, Wad.from_number(500)).transact()

        # and
        assert sai.tub.ink(1) == Wad.from_number(4)
        assert sai.tub.tab(1) == Wad.from_number(500)

        # and
        keeper.approve()

        # when
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(276).value).transact()
        # and
        keeper.check_all_cups()
        # then
        assert sai.tub.ink(1) == Wad.from_number(4)
        assert sai.tub.tab(1) == Wad.from_number(500)

        # when
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(274).value).transact()
        # and
        keeper.check_all_cups()
        # then
        assert sai.tub.ink(1) == Wad(4470802919708029000)
        assert sai.tub.tab(1) == Wad.from_number(500)
