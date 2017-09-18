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

from web3 import Web3, EthereumTesterProvider

from keeper import Address, ERC20Token, Wad
from keeper.api.feed import DSValue
from keeper.api.oasis import SimpleMarket
from keeper.api.token import DSEthToken
from keeper.sai_bite import SaiBite
from tests.conftest import SaiDeployment


class TestSaiBite:
    @staticmethod
    def setup_keeper(sai: SaiDeployment):
        # for Keeper
        keeper = SaiBite.__new__(SaiBite)
        keeper.web3 = sai.web3
        keeper.web3.eth.defaultAccount = keeper.web3.eth.accounts[0]
        keeper.our_address = Address(keeper.web3.eth.defaultAccount)
        keeper.chain = 'unittest'
        keeper.config = None  # intentional, don't know how to deal with config in unit tests yet
        keeper.terminated = False
        keeper.fatal_termination = False
        keeper._last_block_time = None
        keeper._on_block_callback = None

        # for SaiKeeper
        keeper.tub = sai.tub
        keeper.tap = sai.tap
        keeper.top = sai.top
        keeper.otc = SimpleMarket.deploy(keeper.web3)
        keeper.skr = ERC20Token(web3=keeper.web3, address=keeper.tub.skr())
        keeper.sai = ERC20Token(web3=keeper.web3, address=keeper.tub.sai())
        keeper.gem = DSEthToken(web3=keeper.web3, address=keeper.tub.gem())
        ERC20Token.register_token(keeper.tub.skr(), 'SKR')
        ERC20Token.register_token(keeper.tub.sai(), 'SAI')
        ERC20Token.register_token(keeper.tub.gem(), 'WETH')
        return keeper

    def test_should_bite_unsafe_cups_only(self, sai: SaiDeployment):
        # given
        keeper = self.setup_keeper(sai)

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


