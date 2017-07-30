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

from api import Address
from api.conftest import SaiDeployment
from api.feed import DSValue
from api.numeric import Wad, Ray


class TestSai:
    def test_join_and_exit(self, sai: SaiDeployment):
        # given
        assert sai.skr.balance_of(sai.our_address) == Wad(0)
        assert sai.skr.total_supply() == Wad(0)

        # when
        sai.tub.join(Wad.from_number(5))

        # then
        assert sai.skr.balance_of(sai.our_address) == Wad.from_number(5)
        assert sai.skr.total_supply() == Wad.from_number(5)

        # when
        sai.tub.exit(Wad.from_number(4))

        # then
        assert sai.skr.balance_of(sai.our_address) == Wad.from_number(1)
        assert sai.skr.total_supply() == Wad.from_number(1)

    def test_cork_and_hat(self, sai: SaiDeployment):
        # given
        assert sai.tub.hat() == Wad(0)

        # when
        sai.tub.cork(Wad.from_number(150000))

        # then
        assert sai.tub.hat() == Wad.from_number(150000)

    def test_crop_and_tax(self, sai: SaiDeployment):
        # given
        assert sai.tub.tax() == Ray.from_number(1)

        # when
        sai.tub.crop(Ray.from_number(1.00000000000000002))

        # then
        assert sai.tub.tax() == Ray.from_number(1.00000000000000002)

    def test_cuff_and_mat(self, sai: SaiDeployment):
        # given
        assert sai.tub.mat() == Ray.from_number(1)

        # when
        sai.tub.cuff(Ray.from_number(1.5))

        # then
        assert sai.tub.mat() == Ray.from_number(1.5)

    def test_chop_and_axe(self, sai: SaiDeployment):
        # given
        assert sai.tub.axe() == Ray.from_number(1)
        sai.tub.cuff(Ray.from_number(1.5))

        # when
        sai.tub.chop(Ray.from_number(1.2))

        # then
        assert sai.tub.axe() == Ray.from_number(1.2)

    def test_coax_and_way(self, sai: SaiDeployment):
        # given
        assert sai.tub.way() == Ray.from_number(1)

        # when
        sai.tub.coax(Ray.from_number(1.00000000000000007))

        # then
        assert sai.tub.way() == Ray.from_number(1.00000000000000007)

    def test_sai(self, sai: SaiDeployment):
        assert sai.tub.sai() == sai.sai.address

    def test_gem(self, sai: SaiDeployment):
        assert sai.tub.gem() == sai.gem.address

    def test_skr(self, sai: SaiDeployment):
        assert sai.tub.skr() == sai.skr.address

    def test_jug_pip(self, sai: SaiDeployment):
        assert isinstance(sai.tub.jug(), Address)
        assert isinstance(sai.tub.pip(), Address)

    def test_tip(self, sai: SaiDeployment):
        assert isinstance(sai.tub.tip(), Address)

    def test_reg(self, sai: SaiDeployment):
        assert sai.tub.reg() == 0

    def test_per(self, sai: SaiDeployment):
        assert sai.tub.per() == Ray.from_number(1.0)

    def test_tag(self, sai: SaiDeployment):
        # when
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250.45).value)

        # then
        assert sai.tub.tag() == Wad.from_number(250.45)

    def test_open_and_cupi(self, sai: SaiDeployment):
        # when
        sai.tub.open()

        # then
        assert sai.tub.cupi() == 1

    def test_cups(self, sai: SaiDeployment):
        # when
        sai.tub.open()

        # then
        assert sai.tub.cups(1).art == Wad(0)
        assert sai.tub.cups(1).ink == Wad(0)
        assert sai.tub.cups(1).lad == sai.our_address

    @pytest.mark.skip(reason="some issue with safe() - ethereum.tester.TransactionFailed")
    def test_safe(self, sai: SaiDeployment):
        # given
        sai.tub.cuff(Ray.from_number(1.5))
        sai.tub.chop(Ray.from_number(1.2))

        # when
        sai.tub.open()

        # then
        assert sai.tub.safe(1)

    def test_ink(self, sai: SaiDeployment):
        # when
        sai.tub.open()

        # then
        assert sai.tub.ink(1) == Wad(0)

    def test_lad(self, sai: SaiDeployment):
        # when
        sai.tub.open()

        # then
        assert sai.tub.lad(1) == sai.our_address

    def test_give(self, sai: SaiDeployment):
        # given
        sai.tub.open()

        # when
        sai.tub.give(1, Address('0x0101010101020202020203030303030404040404'))

        # then
        assert sai.tub.lad(1) == Address('0x0101010101020202020203030303030404040404')

    @pytest.mark.skip(reason="some issue with safe() - ethereum.tester.TransactionFailed")
    def test_shut(self, sai: SaiDeployment):
        # given
        sai.tub.open()

        # when
        sai.tub.shut(1)

        # then
        assert sai.tub.lad(1) == Address('0x0000000000000000000000000000000000000000')

    @pytest.mark.skip(reason="some issue with safe() - ethereum.tester.TransactionFailed")
    def test_lock_and_free(self, sai: SaiDeployment):
        # given
        sai.tub.open()
        sai.tub.join(Wad.from_number(10))

        # when
        print(sai.tub.cupi())
        sai.tub.lock(1, Wad.from_number(5))

        # then
        assert sai.tub.ink(1) == Wad.from_number(5)

        # when
        sai.tub.free(1, Wad.from_number(3))

        # then
        assert sai.tub.ink(1) == Wad.from_number(2)

    def test_draw_and_wipe(self, sai: SaiDeployment):
        # given
        sai.tub.join(Wad.from_number(10))
        sai.tub.cork(Wad.from_number(100000))
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250.45).value)

        # and
        sai.tub.open()
        sai.tub.lock(1, Wad.from_number(5))

        # when
        sai.tub.draw(1, Wad.from_number(50))

        # then
        assert sai.sai.balance_of(sai.our_address) == Wad.from_number(50)

        # when
        sai.tub.wipe(1, Wad.from_number(30))

        # then
        assert sai.sai.balance_of(sai.our_address) == Wad.from_number(20)
