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

from pymaker import Address
from pymaker.deployment import Deployment
from pymaker.feed import DSValue
from pymaker.numeric import Wad, Ray
from pymaker.sai import Tub, Tap, Top


class TestTub:
    def test_warp_and_era(self, deployment: Deployment):
        # given
        old_era = deployment.tub.era()

        # when
        deployment.tub.warp(30).transact()

        # then
        assert deployment.tub.era() == old_era + 30

    def test_join_and_pie_and_exit(self, deployment: Deployment):
        # given
        assert deployment.skr.balance_of(deployment.our_address) == Wad(0)
        assert deployment.skr.total_supply() == Wad(0)

        # when
        deployment.tub.join(Wad.from_number(5)).transact()

        # then
        assert deployment.skr.balance_of(deployment.our_address) == Wad.from_number(5)
        assert deployment.skr.total_supply() == Wad.from_number(5)
        assert deployment.tub.pie() == Wad.from_number(5)

        # when
        deployment.tub.exit(Wad.from_number(4)).transact()

        # then
        assert deployment.skr.balance_of(deployment.our_address) == Wad.from_number(1)
        assert deployment.skr.total_supply() == Wad.from_number(1)
        assert deployment.tub.pie() == Wad.from_number(1)

    def test_cork_and_hat(self, deployment: Deployment):
        # given
        assert deployment.tub.hat() == Wad(0)

        # when
        deployment.tub.cork(Wad.from_number(150000)).transact()

        # then
        assert deployment.tub.hat() == Wad.from_number(150000)

    def test_crop_and_tax(self, deployment: Deployment):
        # given
        assert deployment.tub.tax() == Ray.from_number(1)

        # when
        deployment.tub.crop(Ray(1000000000000000020000000000)).transact()

        # then
        assert deployment.tub.tax() == Ray(1000000000000000020000000000)

    def test_cuff_and_mat(self, deployment: Deployment):
        # given
        assert deployment.tub.mat() == Ray.from_number(1)

        # when
        deployment.tub.cuff(Ray.from_number(1.5)).transact()

        # then
        assert deployment.tub.mat() == Ray.from_number(1.5)

    def test_chop_and_axe(self, deployment: Deployment):
        # given
        assert deployment.tub.axe() == Ray.from_number(1)
        deployment.tub.cuff(Ray.from_number(1.5)).transact()

        # when
        deployment.tub.chop(Ray.from_number(1.2)).transact()

        # then
        assert deployment.tub.axe() == Ray.from_number(1.2)

    def test_coax_and_way(self, deployment: Deployment):
        # given
        assert deployment.tub.way() == Ray.from_number(1)

        # when
        deployment.tub.coax(Ray(1000000000000000070000000000)).transact()

        # then
        assert deployment.tub.way() == Ray(1000000000000000070000000000)

    def test_sai(self, deployment: Deployment):
        assert deployment.tub.sai() == deployment.sai.address

    def test_sin(self, deployment: Deployment):
        assert deployment.tub.sin() == deployment.sin.address

    def test_gem(self, deployment: Deployment):
        assert deployment.tub.gem() == deployment.gem.address

    def test_skr(self, deployment: Deployment):
        assert deployment.tub.skr() == deployment.skr.address

    def test_jug_pip(self, deployment: Deployment):
        assert isinstance(deployment.tub.jug(), Address)
        assert isinstance(deployment.tub.pip(), Address)

    def test_tip(self, deployment: Deployment):
        assert isinstance(deployment.tub.tip(), Address)

    def test_reg(self, deployment: Deployment):
        assert deployment.tub.reg() == 0

    def test_per(self, deployment: Deployment):
        assert deployment.tub.per() == Ray.from_number(1.0)

    def test_tag(self, deployment: Deployment):
        # when
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250.45).value).transact()

        # then
        assert deployment.tub.tag() == Wad.from_number(250.45)

    def test_drip_and_chi_and_rho(self, deployment: Deployment):
        # given
        deployment.tub.crop(Ray(1000000000000000020000000000)).transact()
        old_chi = deployment.tub.chi()
        old_rho = deployment.tub.rho()

        # when
        deployment.tub.warp(1000).transact()
        deployment.tub.drip().transact()

        # then
        assert deployment.tub.chi() > old_chi
        assert deployment.tub.rho() > old_rho

    def test_prod_and_par_and_tau(self, deployment: Deployment):
        # given
        deployment.tub.coax(Ray(1000000000000000070000000000)).transact()
        old_par = deployment.tub.par()
        old_tau = deployment.tub.tau()

        # when
        deployment.tub.warp(1000).transact()
        deployment.tub.prod().transact()

        # then
        assert deployment.tub.par() > old_par
        assert deployment.tub.tau() > old_tau

    def test_open_and_cupi(self, deployment: Deployment):
        # when
        deployment.tub.open().transact()

        # then
        assert deployment.tub.cupi() == 1

    def test_cups(self, deployment: Deployment):
        # when
        deployment.tub.open().transact()

        # then
        assert deployment.tub.cups(1).art == Wad(0)
        assert deployment.tub.cups(1).ink == Wad(0)
        assert deployment.tub.cups(1).lad == deployment.our_address

    def test_safe(self, deployment: Deployment):
        # given
        deployment.tub.cuff(Ray.from_number(1.5)).transact()
        deployment.tub.chop(Ray.from_number(1.2)).transact()
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # when
        deployment.tub.open().transact()

        # then
        assert deployment.tub.safe(1)

    def test_ink(self, deployment: Deployment):
        # when
        deployment.tub.open().transact()

        # then
        assert deployment.tub.ink(1) == Wad(0)

    def test_lad(self, deployment: Deployment):
        # when
        deployment.tub.open().transact()

        # then
        assert deployment.tub.lad(1) == deployment.our_address

    def test_give(self, deployment: Deployment):
        # given
        deployment.tub.open().transact()

        # when
        deployment.tub.give(1, Address('0x0101010101020202020203030303030404040404')).transact()

        # then
        assert deployment.tub.lad(1) == Address('0x0101010101020202020203030303030404040404')

    def test_shut(self, deployment: Deployment):
        # given
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()
        deployment.tub.open().transact()

        # when
        deployment.tub.shut(1).transact()

        # then
        assert deployment.tub.lad(1) == Address('0x0000000000000000000000000000000000000000')

    def test_lock_and_free(self, deployment: Deployment):
        # given
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()
        deployment.tub.open().transact()
        deployment.tub.join(Wad.from_number(10)).transact()

        # when
        print(deployment.tub.cupi())
        deployment.tub.lock(1, Wad.from_number(5)).transact()

        # then
        assert deployment.tub.ink(1) == Wad.from_number(5)
        assert deployment.tub.air() == Wad.from_number(5)

        # when
        deployment.tub.free(1, Wad.from_number(3)).transact()

        # then
        assert deployment.tub.ink(1) == Wad.from_number(2)
        assert deployment.tub.air() == Wad.from_number(2)

    def test_draw_and_tab_and_ice_and_wipe(self, deployment: Deployment):
        # given
        deployment.tub.join(Wad.from_number(10)).transact()
        deployment.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250.45).value).transact()

        # and
        deployment.tub.open().transact()
        deployment.tub.lock(1, Wad.from_number(5)).transact()

        # when
        deployment.tub.draw(1, Wad.from_number(50)).transact()

        # then
        assert deployment.sai.balance_of(deployment.our_address) == Wad.from_number(50)
        assert deployment.tub.tab(1) == Wad.from_number(50)
        assert deployment.tub.ice() == Wad.from_number(50)

        # when
        deployment.tub.wipe(1, Wad.from_number(30)).transact()

        # then
        assert deployment.sai.balance_of(deployment.our_address) == Wad.from_number(20)
        assert deployment.tub.tab(1) == Wad.from_number(20)
        assert deployment.tub.ice() == Wad.from_number(20)

    def test_bite_and_safe(self, deployment: Deployment):
        # given
        deployment.tub.join(Wad.from_number(10)).transact()
        deployment.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # when
        deployment.tub.open().transact()
        deployment.tub.lock(1, Wad.from_number(4)).transact()
        deployment.tub.draw(1, Wad.from_number(1000)).transact()

        # then
        assert deployment.tub.safe(1)

        # when
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(150).value).transact()

        # then
        assert not deployment.tub.safe(1)

        # when
        deployment.tub.bite(1).transact()

        # then
        assert deployment.tub.safe(1)

    def test_jar_jump_and_gap(self, deployment: Deployment):
        # given
        assert deployment.tub.jar_gap() == Wad.from_number(1)

        # when
        deployment.tub.jar_jump(Wad.from_number(1.05)).transact()

        # then
        assert deployment.tub.jar_gap() == Wad.from_number(1.05)

    def test_jar_bid_and_ask(self, deployment: Deployment):
        # when
        deployment.tub.jar_jump(Wad.from_number(1.05)).transact()

        # then
        assert deployment.tub.jar_bid() == Ray.from_number(0.95)
        assert deployment.tub.jar_ask() == Ray.from_number(1.05)

    def test_comparison(self, deployment: Deployment):
        # expect
        assert deployment.tub == deployment.tub
        assert deployment.tub == Tub(web3=deployment.web3, address=deployment.tub.address)


class TestTap:
    def test_jump_and_gap(self, deployment: Deployment):
        # given
        assert deployment.tap.gap() == Wad.from_number(1)

        # when
        deployment.tap.jump(Wad.from_number(1.05)).transact()

        # then
        assert deployment.tap.gap() == Wad.from_number(1.05)

    def test_woe(self, deployment: Deployment):
        assert deployment.tap.woe() == Wad(0)

    def test_fog(self, deployment: Deployment):
        assert deployment.tap.fog() == Wad(0)

    def test_joy(self, deployment: Deployment):
        assert deployment.tap.joy() == Wad(0)

    def test_s2s_and_bid_and_ask(self, deployment: Deployment):
        # when
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(500).value).transact()
        deployment.tap.jump(Wad.from_number(1.05)).transact()

        # then
        assert deployment.tap.bid() == Wad.from_number(475)
        assert deployment.tap.s2s() == Wad.from_number(500)
        assert deployment.tap.ask() == Wad.from_number(525)

    def test_joy_and_boom(self, deployment: Deployment):
        # given
        deployment.tub.join(Wad.from_number(10)).transact()
        deployment.tub.cork(Wad.from_number(100000)).transact()
        deployment.tub.crop(Ray(1000100000000000000000000000)).transact()
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # and
        deployment.tub.open().transact()
        deployment.tub.lock(1, Wad.from_number(4)).transact()
        deployment.tub.draw(1, Wad.from_number(1000)).transact()

        # when
        deployment.tub.drip().transact()
        deployment.tub.warp(3600).transact()
        deployment.tub.drip().transact()

        # then
        assert deployment.skr.balance_of(deployment.our_address) == Wad.from_number(6)
        assert deployment.tap.joy() == Wad(433303616582911495481)

        # when
        deployment.tap.boom(Wad.from_number(1)).transact()

        # then
        assert deployment.skr.balance_of(deployment.our_address) == Wad.from_number(5)
        assert deployment.tap.joy() == Wad(183303616582911495481)

    def test_fog_and_woe_and_bust(self, deployment: Deployment):
        # given
        deployment.tub.join(Wad.from_number(10)).transact()
        deployment.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # and
        deployment.tub.open().transact()
        deployment.tub.lock(1, Wad.from_number(4)).transact()
        deployment.tub.draw(1, Wad.from_number(1000)).transact()

        # and
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(150).value).transact()

        # when
        deployment.tub.bite(1).transact()

        # then
        assert deployment.tap.fog() == Wad.from_number(4)
        assert deployment.tap.woe() == Wad.from_number(1000)
        assert deployment.skr.balance_of(deployment.our_address) == Wad.from_number(6)
        assert deployment.sai.balance_of(deployment.our_address) == Wad.from_number(1000)

        # when
        deployment.tap.bust(Wad.from_number(2)).transact()
        assert deployment.tap.fog() == Wad.from_number(2)
        assert deployment.tap.woe() == Wad.from_number(700)
        assert deployment.skr.balance_of(deployment.our_address) == Wad.from_number(8)
        assert deployment.sai.balance_of(deployment.our_address) == Wad.from_number(700)

    def test_comparison(self, deployment: Deployment):
        # expect
        assert deployment.tap == deployment.tap
        assert deployment.tap == Tap(web3=deployment.web3, address=deployment.tap.address)
        assert deployment.tap != Tap(web3=deployment.web3, address=deployment.tub.address)


class TestTop:
    def test_comparison(self, deployment: Deployment):
        # expect
        assert deployment.top == deployment.top
        assert deployment.top == Top(web3=deployment.web3, address=deployment.top.address)
        assert deployment.top != Top(web3=deployment.web3, address=deployment.tub.address)

    def test_default_fix(self, deployment: Deployment):
        # expect
        assert deployment.top.fix() == Ray.from_number(0)

    def test_cage_without_price(self, deployment: Deployment):
        # given
        deployment.tub.join(Wad.from_number(10)).transact()
        deployment.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # and
        deployment.tub.open().transact()
        deployment.tub.lock(1, Wad.from_number(4)).transact()
        deployment.tub.draw(1, Wad.from_number(1000)).transact()

        # when
        deployment.top.cage().transact()

        # then
        assert deployment.top.fix() == Ray.from_number(0.004)

    def test_cage_with_price(self, deployment: Deployment):
        # given
        deployment.tub.join(Wad.from_number(10)).transact()
        deployment.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # and
        deployment.tub.open().transact()
        deployment.tub.lock(1, Wad.from_number(4)).transact()
        deployment.tub.draw(1, Wad.from_number(1000)).transact()

        # when
        deployment.top.cage(Wad.from_number(200)).transact()

        # then
        assert deployment.top.fix() == Ray.from_number(0.005)

    def test_cash(self, deployment: Deployment):
        # given
        deployment.tub.join(Wad.from_number(10)).transact()
        deployment.tub.cork(Wad.from_number(100000)).transact()
        DSValue(web3=deployment.web3, address=deployment.tub.pip()).poke_with_int(Wad.from_number(250).value).transact()

        # and
        deployment.tub.open().transact()
        deployment.tub.lock(1, Wad.from_number(4)).transact()
        deployment.tub.draw(1, Wad.from_number(1000)).transact()

        # and
        gem_before = deployment.gem.balance_of(deployment.our_address)

        # when
        deployment.top.cage().transact()
        deployment.top.cash().transact()

        # then
        gem_after = deployment.gem.balance_of(deployment.our_address)
        assert gem_after - gem_before == Wad.from_number(4)
