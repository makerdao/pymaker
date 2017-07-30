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

from api.numeric import Wad, Ray


class TestSai:
    def test_join_and_exit(self, sai):
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

    def test_cork_and_hat(self, sai):
        # given
        assert sai.tub.hat() == Wad(0)

        # when
        sai.tub.cork(Wad.from_number(150000))

        # then
        assert sai.tub.hat() == Wad.from_number(150000)

    def test_crop_and_tax(self, sai):
        # given
        assert sai.tub.tax() == Ray.from_number(1)

        # when
        sai.tub.crop(Ray.from_number(1.00000000000000002))

        # then
        assert sai.tub.tax() == Ray.from_number(1.00000000000000002)
