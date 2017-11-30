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
from keeper.sai_bite import SaiBite
from tests.conftest import SaiDeployment
from tests.helper import args, captured_output


class TestSaiBite:
    def test_should_not_start_without_eth_from_argument(self, sai: SaiDeployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiBite(args=args(f""), web3=sai.web3)

        # then
        assert "error: the following arguments are required: --eth-from" in err.getvalue()

    def test_should_not_start_without_tub_address_argument(self, sai: SaiDeployment):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                SaiBite(args=args(f"--eth-from {sai.web3.eth.defaultAccount}"), web3=sai.web3)

        # then
        assert "error: the following arguments are required: --tub-address" in err.getvalue()

    def test_should_bite_unsafe_cups_only(self, sai: SaiDeployment):
        # given
        keeper = SaiBite(args=args(f"--eth-from {sai.web3.eth.defaultAccount} --tub-address {sai.tub.address}"),
                         web3=sai.web3)

        # and
        sai.tub.join(Wad.from_number(10)).transact()
        sai.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # and
        sai.tub.open().transact()
        sai.tub.lock(1, Wad.from_number(4)).transact()
        sai.tub.draw(1, Wad.from_number(1000)).transact()

        # and
        assert sai.tub.safe(1)

        # when
        keeper.check_all_cups()

        # then
        assert sai.tub.safe(1)
        assert sai.tub.tab(1) == Wad.from_number(1000)

        # when
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(150).value).transact()

        # and
        assert not sai.tub.safe(1)

        # and
        keeper.check_all_cups()

        # then
        assert sai.tub.safe(1)
        assert sai.tub.tab(1) == Wad.from_number(0)
