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


class TestTub:
    def test_warp_and_era(self, sai: SaiDeployment):
        # given
        old_era = sai.tub.era()

        # when
        sai.tub.warp(30).transact()

        # then
        assert sai.tub.era() == old_era + 30

    def test_join_and_pie_and_exit(self, sai: SaiDeployment):
        # given
        assert sai.skr.balance_of(sai.our_address) == Wad(0)
        assert sai.skr.total_supply() == Wad(0)

        # when
        sai.tub.join(Wad.from_number(5)).transact()

        # then
        assert sai.skr.balance_of(sai.our_address) == Wad.from_number(5)
        assert sai.skr.total_supply() == Wad.from_number(5)
        assert sai.tub.pie() == Wad.from_number(5)

        # when
        sai.tub.exit(Wad.from_number(4)).transact()

        # then
        assert sai.skr.balance_of(sai.our_address) == Wad.from_number(1)
        assert sai.skr.total_supply() == Wad.from_number(1)
        assert sai.tub.pie() == Wad.from_number(1)

    def test_cork_and_hat(self, sai: SaiDeployment):
        # given
        assert sai.tub.hat() == Wad(0)

        # when
        sai.tub.cork(Wad.from_number(150000)).transact()

        # then
        assert sai.tub.hat() == Wad.from_number(150000)

    def test_crop_and_tax(self, sai: SaiDeployment):
        # given
        assert sai.tub.tax() == Ray.from_number(1)

        # when
        sai.tub.crop(Ray(1000000000000000020000000000)).transact()

        # then
        assert sai.tub.tax() == Ray(1000000000000000020000000000)

    def test_cuff_and_mat(self, sai: SaiDeployment):
        # given
        assert sai.tub.mat() == Ray.from_number(1)

        # when
        sai.tub.cuff(Ray.from_number(1.5)).transact()

        # then
        assert sai.tub.mat() == Ray.from_number(1.5)

    def test_chop_and_axe(self, sai: SaiDeployment):
        # given
        assert sai.tub.axe() == Ray.from_number(1)
        sai.tub.cuff(Ray.from_number(1.5)).transact()

        # when
        sai.tub.chop(Ray.from_number(1.2)).transact()

        # then
        assert sai.tub.axe() == Ray.from_number(1.2)

    def test_coax_and_way(self, sai: SaiDeployment):
        # given
        assert sai.tub.way() == Ray.from_number(1)

        # when
        sai.tub.coax(Ray(1000000000000000070000000000)).transact()

        # then
        assert sai.tub.way() == Ray(1000000000000000070000000000)

    def test_sai(self, sai: SaiDeployment):
        assert sai.tub.sai() == sai.sai.address

    def test_sin(self, sai: SaiDeployment):
        assert sai.tub.sin() == sai.sin.address

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
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250.45).value).transact()

        # then
        assert sai.tub.tag() == Wad.from_number(250.45)

    def test_drip_and_chi_and_rho(self, sai: SaiDeployment):
        # given
        sai.tub.crop(Ray(1000000000000000020000000000)).transact()
        old_chi = sai.tub.chi()
        old_rho = sai.tub.rho()

        # when
        sai.tub.warp(1000).transact()
        sai.tub.drip().transact()

        # then
        assert sai.tub.chi() > old_chi
        assert sai.tub.rho() > old_rho

    def test_prod_and_par_and_tau(self, sai: SaiDeployment):
        # given
        sai.tub.coax(Ray(1000000000000000070000000000)).transact()
        old_par = sai.tub.par()
        old_tau = sai.tub.tau()

        # when
        sai.tub.warp(1000).transact()
        sai.tub.prod().transact()

        # then
        assert sai.tub.par() > old_par
        assert sai.tub.tau() > old_tau

    def test_open_and_cupi(self, sai: SaiDeployment):
        # when
        sai.tub.open().transact()

        # then
        assert sai.tub.cupi() == 1

    def test_cups(self, sai: SaiDeployment):
        # when
        sai.tub.open().transact()

        # then
        assert sai.tub.cups(1).art == Wad(0)
        assert sai.tub.cups(1).ink == Wad(0)
        assert sai.tub.cups(1).lad == sai.our_address

    def test_safe(self, sai: SaiDeployment):
        # given
        sai.tub.cuff(Ray.from_number(1.5)).transact()
        sai.tub.chop(Ray.from_number(1.2)).transact()
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # when
        sai.tub.open().transact()

        # then
        assert sai.tub.safe(1)

    def test_ink(self, sai: SaiDeployment):
        # when
        sai.tub.open().transact()

        # then
        assert sai.tub.ink(1) == Wad(0)

    def test_lad(self, sai: SaiDeployment):
        # when
        sai.tub.open().transact()

        # then
        assert sai.tub.lad(1) == sai.our_address

    def test_give(self, sai: SaiDeployment):
        # given
        sai.tub.open().transact()

        # when
        sai.tub.give(1, Address('0x0101010101020202020203030303030404040404')).transact()

        # then
        assert sai.tub.lad(1) == Address('0x0101010101020202020203030303030404040404')

    def test_shut(self, sai: SaiDeployment):
        # given
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()
        sai.tub.open().transact()

        # when
        sai.tub.shut(1).transact()

        # then
        assert sai.tub.lad(1) == Address('0x0000000000000000000000000000000000000000')

    def test_lock_and_free(self, sai: SaiDeployment):
        # given
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()
        sai.tub.open().transact()
        sai.tub.join(Wad.from_number(10)).transact()

        # when
        print(sai.tub.cupi())
        sai.tub.lock(1, Wad.from_number(5)).transact()

        # then
        assert sai.tub.ink(1) == Wad.from_number(5)
        assert sai.tub.air() == Wad.from_number(5)

        # when
        sai.tub.free(1, Wad.from_number(3)).transact()

        # then
        assert sai.tub.ink(1) == Wad.from_number(2)
        assert sai.tub.air() == Wad.from_number(2)

    def test_draw_and_tab_and_ice_and_wipe(self, sai: SaiDeployment):
        # given
        sai.tub.join(Wad.from_number(10)).transact()
        sai.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250.45).value).transact()

        # and
        sai.tub.open().transact()
        sai.tub.lock(1, Wad.from_number(5)).transact()

        # when
        sai.tub.draw(1, Wad.from_number(50)).transact()

        # then
        assert sai.sai.balance_of(sai.our_address) == Wad.from_number(50)
        assert sai.tub.tab(1) == Wad.from_number(50)
        assert sai.tub.ice() == Wad.from_number(50)

        # when
        sai.tub.wipe(1, Wad.from_number(30)).transact()

        # then
        assert sai.sai.balance_of(sai.our_address) == Wad.from_number(20)
        assert sai.tub.tab(1) == Wad.from_number(20)
        assert sai.tub.ice() == Wad.from_number(20)

    def test_bite_and_safe(self, sai: SaiDeployment):
        # given
        sai.tub.join(Wad.from_number(10)).transact()
        sai.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # when
        sai.tub.open().transact()
        sai.tub.lock(1, Wad.from_number(4)).transact()
        sai.tub.draw(1, Wad.from_number(1000)).transact()

        # then
        assert sai.tub.safe(1)

        # when
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(150).value).transact()

        # then
        assert not sai.tub.safe(1)

        # when
        sai.tub.bite(1).transact()

        # then
        assert sai.tub.safe(1)

    def test_jar_jump_and_gap(self, sai: SaiDeployment):
        # given
        assert sai.tub.jar_gap() == Wad.from_number(1)

        # when
        sai.tub.jar_jump(Wad.from_number(1.05)).transact()

        # then
        assert sai.tub.jar_gap() == Wad.from_number(1.05)

    def test_jar_bid_and_ask(self, sai: SaiDeployment):
        # when
        sai.tub.jar_jump(Wad.from_number(1.05)).transact()

        # then
        assert sai.tub.jar_bid() == Ray.from_number(0.95)
        assert sai.tub.jar_ask() == Ray.from_number(1.05)


class TestTap:
    def test_jump_and_gap(self, sai: SaiDeployment):
        # given
        assert sai.tap.gap() == Wad.from_number(1)

        # when
        sai.tap.jump(Wad.from_number(1.05)).transact()

        # then
        assert sai.tap.gap() == Wad.from_number(1.05)

    def test_woe(self, sai: SaiDeployment):
        assert sai.tap.woe() == Wad(0)

    def test_fog(self, sai: SaiDeployment):
        assert sai.tap.fog() == Wad(0)

    def test_joy(self, sai: SaiDeployment):
        assert sai.tap.joy() == Wad(0)

    def test_s2s_and_bid_and_ask(self, sai: SaiDeployment):
        # when
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        sai.tap.jump(Wad.from_number(1.05)).transact()

        # then
        assert sai.tap.bid() == Wad.from_number(475)
        assert sai.tap.s2s() == Wad.from_number(500)
        assert sai.tap.ask() == Wad.from_number(525)

    def test_joy_and_boom(self, sai: SaiDeployment):
        # given
        sai.tub.join(Wad.from_number(10)).transact()
        sai.tub.cork(Wad.from_number(100000)).transact()
        sai.tub.crop(Ray(1000100000000000000000000000)).transact()
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # and
        sai.tub.open().transact()
        sai.tub.lock(1, Wad.from_number(4)).transact()
        sai.tub.draw(1, Wad.from_number(1000)).transact()

        # when
        sai.tub.drip().transact()
        sai.tub.warp(3600).transact()
        sai.tub.drip().transact()

        # then
        assert sai.skr.balance_of(sai.our_address) == Wad.from_number(6)
        assert sai.tap.joy() == Wad(433303616582911495481)

        # when
        sai.tap.boom(Wad.from_number(1)).transact()

        # then
        assert sai.skr.balance_of(sai.our_address) == Wad.from_number(5)
        assert sai.tap.joy() == Wad(183303616582911495481)

    def test_fog_and_woe_and_bust(self, sai: SaiDeployment):
        # given
        sai.tub.join(Wad.from_number(10)).transact()
        sai.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # and
        sai.tub.open().transact()
        sai.tub.lock(1, Wad.from_number(4)).transact()
        sai.tub.draw(1, Wad.from_number(1000)).transact()

        # and
        DSValue(web3=sai.web3, address=sai.tub.pip()).poke_with_int(Wad.from_number(150).value).transact()

        # when
        sai.tub.bite(1).transact()

        # then
        assert sai.tap.fog() == Wad.from_number(4)
        assert sai.tap.woe() == Wad.from_number(1000)
        assert sai.skr.balance_of(sai.our_address) == Wad.from_number(6)
        assert sai.sai.balance_of(sai.our_address) == Wad.from_number(1000)

        # when
        sai.tap.bust(Wad.from_number(2)).transact()
        assert sai.tap.fog() == Wad.from_number(2)
        assert sai.tap.woe() == Wad.from_number(700)
        assert sai.skr.balance_of(sai.our_address) == Wad.from_number(8)
        assert sai.sai.balance_of(sai.our_address) == Wad.from_number(700)
