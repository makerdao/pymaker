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

from keeper import Wad
from keeper.api.feed import DSValue
from keeper.sai_bite import SaiBite
from tests.conftest import SaiDeployment
from tests.helper import args


class TestSaiBite:
    def test_should_bite_unsafe_cups_only(self, sai: SaiDeployment):
        # given
        keeper = SaiBite(args=args(f"--eth-from {sai.web3.eth.defaultAccount}"),
                         web3=sai.web3, config=sai.get_config())

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
