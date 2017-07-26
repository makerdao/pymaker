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

from api.numeric import Wad, Ray


class TestWad:
    def test_should_support_negative_values(self):
        Wad(-1)

    def test_should_support_values_greater_than_uint256(self):
        Wad(2**256)
        Wad(2**256 + 1)
        Wad(2**512)

    def test_should_format_to_string_nicely(self):
        assert str(Wad(1)) == "0.000000000000000001"
        assert str(Wad(500000000000000000)) == "0.500000000000000000"
        assert str(Wad(1500000000000000000)) == "1.500000000000000000"
        assert str(Wad(-1500000000000000000)) == "-1.500000000000000000"
        assert str(Wad(-500000000000000000)) == "-0.500000000000000000"
        assert str(Wad(-1)) == "-0.000000000000000001"

    def test_add(self):
        assert Wad(1) + Wad(2) == Wad(3)

    def test_add_should_not_work_with_rays(self):
        with pytest.raises(ArithmeticError):
            Wad(1) + Ray(2)

    def test_add_should_not_work_with_ints(self):
        with pytest.raises(ArithmeticError):
            Wad(1) + 2

    def test_subtract(self):
        assert Wad(10) - Wad(2) == Wad(8)
        assert Wad(1) - Wad(2) == Wad(-1)

    def test_subtract_should_not_work_with_rays(self):
        with pytest.raises(ArithmeticError):
            Wad(10) - Ray(2)

    def test_should_compare_wads_with_each_other(self):
        assert Wad(1000) == Wad(1000)
        assert Wad(1000) != Wad(999)
        assert Wad(1000) > Wad(999)
        assert Wad(999) < Wad(1000)
        assert Wad(999) <= Wad(1000)
        assert Wad(1000) <= Wad(1000)
        assert Wad(1000) >= Wad(1000)
        assert Wad(1000) >= Wad(999)

    def test_should_reject_comparison_with_rays(self):
        with pytest.raises(ArithmeticError):
            assert Wad(1000) == Ray(1000)
        with pytest.raises(ArithmeticError):
            assert Wad(1000) != Ray(999)
        with pytest.raises(ArithmeticError):
            assert Wad(1000) > Ray(999)
        with pytest.raises(ArithmeticError):
            assert Wad(999) < Ray(1000)
        with pytest.raises(ArithmeticError):
            assert Wad(999) <= Ray(1000)
        with pytest.raises(ArithmeticError):
            assert Wad(1000) <= Ray(1000)
        with pytest.raises(ArithmeticError):
            assert Wad(1000) >= Ray(1000)
        with pytest.raises(ArithmeticError):
            assert Wad(1000) >= Ray(999)

    def test_should_reject_comparison_with_ints(self):
        with pytest.raises(ArithmeticError):
            assert Wad(1000) == 100
        with pytest.raises(ArithmeticError):
            assert Wad(1000) != 999
        with pytest.raises(ArithmeticError):
            assert Wad(1000) > 999
        with pytest.raises(ArithmeticError):
            assert Wad(999) < 1000
        with pytest.raises(ArithmeticError):
            assert Wad(999) <= 1000
        with pytest.raises(ArithmeticError):
            assert Wad(1000) <= 1000
        with pytest.raises(ArithmeticError):
            assert Wad(1000) >= 1000
        with pytest.raises(ArithmeticError):
            assert Wad(1000) >= 999

    def test_min_value(self):
        assert Wad.min(Wad(10), Wad(20)) == Wad(10)
        assert Wad.min(Wad(25), Wad(15)) == Wad(15)
        assert Wad.min(Wad(25), Wad(15), Wad(5)) == Wad(5)

    def test_min_value_should_reject_comparison_with_rays(self):
        with pytest.raises(ArithmeticError):
            Wad.min(Wad(10), Ray(20))
        with pytest.raises(ArithmeticError):
            Wad.min(Ray(25), Wad(15))

    def test_min_value_should_reject_comparison_with_ints(self):
        with pytest.raises(ArithmeticError):
            Wad.min(Wad(10), 20)
        with pytest.raises(ArithmeticError):
            Wad.min(20, Wad(10))

    def test_max_value(self):
        assert Wad.max(Wad(10), Wad(20)) == Wad(20)
        assert Wad.max(Wad(25), Wad(15)) == Wad(25)
        assert Wad.max(Wad(25), Wad(15), Wad(40)) == Wad(40)

    def test_max_value_should_reject_comparison_with_rays(self):
        with pytest.raises(ArithmeticError):
            Wad.max(Wad(10), Ray(20))
        with pytest.raises(ArithmeticError):
            Wad.max(Wad(25), Ray(15))

    def test_max_value_should_reject_comparison_with_ints(self):
        with pytest.raises(ArithmeticError):
            Wad.max(Wad(10), 20)
        with pytest.raises(ArithmeticError):
            Wad.max(15, Wad(25))


class TestRay:
    def test_should_support_negative_values(self):
        Ray(-1)

    def test_should_support_values_greater_than_uint256(self):
        Ray(2**256)
        Ray(2**256 + 1)
        Ray(2**512)

    def test_should_format_to_string_nicely(self):
        assert str(Ray(1)) == "0.000000000000000000000000001"
        assert str(Ray(500000000000000000000000000)) == "0.500000000000000000000000000"
        assert str(Ray(1500000000000000000000000000)) == "1.500000000000000000000000000"
        assert str(Ray(-1500000000000000000000000000)) == "-1.500000000000000000000000000"
        assert str(Ray(-500000000000000000000000000)) == "-0.500000000000000000000000000"
        assert str(Ray(-1)) == "-0.000000000000000000000000001"

    def test_add(self):
        assert Ray(1) + Ray(2) == Ray(3)

    def test_add_should_not_work_with_wads(self):
        with pytest.raises(ArithmeticError):
            Ray(1) + Wad(2)

    def test_add_should_not_work_with_ints(self):
        with pytest.raises(ArithmeticError):
            Ray(1) + 2

    def test_subtract(self):
        assert Ray(10) - Ray(2) == Ray(8)
        assert Ray(1) - Ray(2) == Ray(-1)

    def test_subtract_should_not_work_with_wads(self):
        with pytest.raises(ArithmeticError):
            Ray(10) - Wad(2)

    def test_should_compare_rays_with_each_other(self):
        assert Ray(1000) == Ray(1000)
        assert Ray(1000) != Ray(999)
        assert Ray(1000) > Ray(999)
        assert Ray(999) < Ray(1000)
        assert Ray(999) <= Ray(1000)
        assert Ray(1000) <= Ray(1000)
        assert Ray(1000) >= Ray(1000)
        assert Ray(1000) >= Ray(999)

    def test_should_reject_comparison_with_wads(self):
        with pytest.raises(ArithmeticError):
            assert Ray(1000) == Wad(1000)
        with pytest.raises(ArithmeticError):
            assert Ray(1000) != Wad(999)
        with pytest.raises(ArithmeticError):
            assert Ray(1000) > Wad(999)
        with pytest.raises(ArithmeticError):
            assert Ray(999) < Wad(1000)
        with pytest.raises(ArithmeticError):
            assert Ray(999) <= Wad(1000)
        with pytest.raises(ArithmeticError):
            assert Ray(1000) <= Wad(1000)
        with pytest.raises(ArithmeticError):
            assert Ray(1000) >= Wad(1000)
        with pytest.raises(ArithmeticError):
            assert Ray(1000) >= Wad(999)

    def test_should_reject_comparison_with_ints(self):
        with pytest.raises(ArithmeticError):
            assert Ray(1000) == 100
        with pytest.raises(ArithmeticError):
            assert Ray(1000) != 999
        with pytest.raises(ArithmeticError):
            assert Ray(1000) > 999
        with pytest.raises(ArithmeticError):
            assert Ray(999) < 1000
        with pytest.raises(ArithmeticError):
            assert Ray(999) <= 1000
        with pytest.raises(ArithmeticError):
            assert Ray(1000) <= 1000
        with pytest.raises(ArithmeticError):
            assert Ray(1000) >= 1000
        with pytest.raises(ArithmeticError):
            assert Ray(1000) >= 999

    def test_min_value(self):
        assert Ray.min(Ray(10), Ray(20)) == Ray(10)
        assert Ray.min(Ray(25), Ray(15)) == Ray(15)
        assert Ray.min(Ray(25), Ray(15), Ray(5)) == Ray(5)

    def test_min_value_should_reject_comparison_with_wads(self):
        with pytest.raises(ArithmeticError):
            Ray.min(Ray(10), Wad(20))
        with pytest.raises(ArithmeticError):
            Ray.min(Wad(25), Ray(15))

    def test_min_value_should_reject_comparison_with_ints(self):
        with pytest.raises(ArithmeticError):
            Ray.min(Ray(10), 20)
        with pytest.raises(ArithmeticError):
            Ray.min(20, Ray(10))

    def test_max_value(self):
        assert Ray.max(Ray(10), Ray(20)) == Ray(20)
        assert Ray.max(Ray(25), Ray(15)) == Ray(25)
        assert Ray.max(Ray(25), Ray(15), Ray(40)) == Ray(40)

    def test_max_value_should_reject_comparison_with_wads(self):
        with pytest.raises(ArithmeticError):
            Ray.max(Ray(10), Wad(20))
        with pytest.raises(ArithmeticError):
            Ray.max(Ray(25), Wad(15))

    def test_max_value_should_reject_comparison_with_ints(self):
        with pytest.raises(ArithmeticError):
            Ray.max(Ray(10), 20)
        with pytest.raises(ArithmeticError):
            Ray.max(15, Ray(25))
