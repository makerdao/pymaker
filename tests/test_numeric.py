# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
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

from pymaker.numeric import Wad, Ray, Rad
from tests.helpers import is_hashable


class TestWad:
    def test_should_support_negative_values(self):
        Wad(-1)

    def test_should_support_values_greater_than_uint256(self):
        Wad(2**256)
        Wad(2**256 + 1)
        Wad(2**512)

    def test_should_instantiate_from_a_wad(self):
        assert Wad(Wad(1)) == Wad(1)

    def test_should_instantiate_from_a_ray(self):
        assert Wad(Ray(10000000000000001010101010101)) == Wad(10000000000000001010)
        assert Wad(Ray(10000000000000001019999999999)) == Wad(10000000000000001019)

    def test_should_instantiate_from_an_int(self):
        assert Wad(10).value == 10

    def test_should_fail_to_instantiate_from_a_float(self):
        with pytest.raises(ArithmeticError):
            assert Wad(10.5)

    def test_should_format_to_string_nicely(self):
        assert str(Wad(1)) == "0.000000000000000001"
        assert str(Wad(500000000000000000)) == "0.500000000000000000"
        assert str(Wad(1500000000000000000)) == "1.500000000000000000"
        assert str(Wad(-1500000000000000000)) == "-1.500000000000000000"
        assert str(Wad(-500000000000000000)) == "-0.500000000000000000"
        assert str(Wad(-1)) == "-0.000000000000000001"

    def test_should_have_nice_printable_representation(self):
        for wad in [Wad(1), Wad(100), Wad.from_number(2.5), Wad(-1)]:
            assert repr(wad) == f"Wad({wad.value})"

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

    def test_multiply(self):
        assert Wad.from_number(2) * Wad.from_number(3) == Wad.from_number(6)
        assert Wad.from_number(2) * Wad(3) == Wad(6)
        assert Wad.from_number(2.5) * Wad(3) == Wad(7)
        assert Wad.from_number(2.99999) * Wad(3) == Wad(8)

    def test_multiply_by_ray(self):
        assert Wad.from_number(2) * Ray.from_number(3) == Wad.from_number(6)
        assert Wad.from_number(2) * Ray(3) == Wad(0)
        assert Wad(2) * Ray(499999999999999999999999999) == Wad(0)
        assert Wad(2) * Ray(500000000000000000000000000) == Wad(1)
        assert Wad(2) * Ray(999999999999999999999999999) == Wad(1)
        assert Wad(2) * Ray(1000000000000000000000000000) == Wad(2)

    def test_multiply_by_int(self):
        assert Wad.from_number(2) * 3 == Wad.from_number(6)
        assert Wad.from_number(2) * 1 == Wad.from_number(2)

    def test_should_fail_to_multiply_by_float(self):
        with pytest.raises(ArithmeticError):
            Wad(2) * 3.0

    def test_divide(self):
        assert Wad.from_number(4) / Wad.from_number(2) == Wad.from_number(2)
        assert Wad(4) / Wad.from_number(2) == Wad(2)
        assert Wad(3) / Wad.from_number(2) == Wad(1)
        assert Wad(39) / Wad.from_number(20) == Wad(1)
        assert Wad(40) / Wad.from_number(20) == Wad(2)
        assert Wad.from_number(0.2) / Wad.from_number(0.1) == Wad.from_number(2)

    def test_should_fail_to_divide_by_rays(self):
        with pytest.raises(ArithmeticError):
            Wad(4) / Ray(2)

    def test_should_fail_to_divide_by_ints(self):
        with pytest.raises(ArithmeticError):
            Wad(4) / 2

    def test_should_support_abs(self):
        assert abs(Wad(1000)) == Wad(1000)
        assert abs(Wad(0)) == Wad(0)
        assert abs(Wad(-1000)) == Wad(1000)

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

    def test_should_cast_to_int(self):
        assert int(Wad.from_number(-4.5)) == -4
        assert int(Wad.from_number(0.99)) == 0
        assert int(Wad.from_number(1)) == 1
        assert int(Wad.from_number(1.0)) == 1
        assert int(Wad.from_number(1.5)) == 1
        assert int(Wad.from_number(1.9999999999)) == 1

    def test_should_cast_to_float(self):
        assert float(Wad.from_number(-4.5)) == -4.5
        assert float(Wad.from_number(0.99)) == 0.99
        assert float(Wad.from_number(1)) == 1.0
        assert float(Wad.from_number(1.0)) == 1.0
        assert float(Wad.from_number(1.5)) == 1.5
        assert float(Wad.from_number(1.9999999999)) == 1.9999999999

    def test_should_be_hashable(self):
        assert is_hashable(Wad(123))

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

    def test_round(self):
        assert round(Wad.from_number(123.4567), 2) == Wad.from_number(123.46)
        assert round(Wad.from_number(123.4567), 0) == Wad.from_number(123.0)
        assert round(Wad.from_number(123.4567), -2) == Wad.from_number(100.0)

    def test_round_inequality(self):
        # should hold for all x, ndigits
        x = Wad.from_number(7654.321)
        ndigits = 1
        round_difference = x - round(x, ndigits)
        round_distance = Wad(abs(round_difference.value))
        assert round_distance <= Wad.from_number(0.5 * 10**(-ndigits))    


class TestRay:
    def test_should_support_negative_values(self):
        Ray(-1)

    def test_should_support_values_greater_than_uint256(self):
        Ray(2**256)
        Ray(2**256 + 1)
        Ray(2**512)

    def test_should_instantiate_from_a_ray(self):
        assert Ray(Ray(1)) == Ray(1)

    def test_should_instantiate_from_a_wad(self):
        assert Ray(Wad(10000000000000000000)) == Ray(10000000000000000000000000000)

    def test_should_instantiate_from_an_int(self):
        assert Ray(10).value == 10

    def test_should_fail_to_instantiate_from_a_float(self):
        with pytest.raises(ArithmeticError):
            assert Ray(10.5)

    def test_should_format_to_string_nicely(self):
        assert str(Ray(1)) == "0.000000000000000000000000001"
        assert str(Ray(500000000000000000000000000)) == "0.500000000000000000000000000"
        assert str(Ray(1500000000000000000000000000)) == "1.500000000000000000000000000"
        assert str(Ray(-1500000000000000000000000000)) == "-1.500000000000000000000000000"
        assert str(Ray(-500000000000000000000000000)) == "-0.500000000000000000000000000"
        assert str(Ray(-1)) == "-0.000000000000000000000000001"

    def test_should_have_nice_printable_representation(self):
        for ray in [Ray(1), Ray(100), Ray.from_number(2.5), Ray(-1)]:
            assert repr(ray) == f"Ray({ray.value})"

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

    def test_multiply(self):
        assert Ray.from_number(2) * Ray.from_number(3) == Ray.from_number(6)
        assert Ray.from_number(2) * Ray(3) == Ray(6)
        assert Ray.from_number(2.5) * Ray(3) == Ray(7)
        assert Ray.from_number(2.99999) * Ray(3) == Ray(8)

    def test_multiply_by_wad(self):
        assert Ray.from_number(2) * Wad.from_number(3) == Ray.from_number(6)
        assert Ray.from_number(2) * Wad(3) == Ray(6000000000)
        assert Ray(2) * Wad(3) == Ray(0)
        assert Ray(2) * Wad(999999999999999999) == Ray(1)
        assert Ray(2) * Wad(1000000000000000000) == Ray(2)

    def test_multiply_by_int(self):
        assert Ray.from_number(2) * 3 == Ray.from_number(6)
        assert Ray.from_number(2) * 1 == Ray.from_number(2)

    def test_should_fail_to_multiply_by_float(self):
        with pytest.raises(ArithmeticError):
            Ray(2) * 3.0

    def test_divide(self):
        assert Ray.from_number(4) / Ray.from_number(2) == Ray.from_number(2)
        assert Ray(4) / Ray.from_number(2) == Ray(2)
        assert Ray(3) / Ray.from_number(2) == Ray(1)
        assert Ray(39) / Ray.from_number(20) == Ray(1)
        assert Ray(40) / Ray.from_number(20) == Ray(2)
        assert Ray.from_number(0.2) / Ray.from_number(0.1) == Ray.from_number(2)

    def test_should_fail_to_divide_by_wads(self):
        with pytest.raises(ArithmeticError):
            Ray(4) / Wad(2)

    def test_should_fail_to_divide_by_ints(self):
        with pytest.raises(ArithmeticError):
            Ray(4) / 2

    def test_should_support_abs(self):
        assert abs(Ray(1000)) == Ray(1000)
        assert abs(Ray(0)) == Ray(0)
        assert abs(Ray(-1000)) == Ray(1000)

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

    def test_should_cast_to_int(self):
        assert int(Ray.from_number(-4.5)) == -4
        assert int(Ray.from_number(0.99)) == 0
        assert int(Ray.from_number(1)) == 1
        assert int(Ray.from_number(1.0)) == 1
        assert int(Ray.from_number(1.5)) == 1
        assert int(Ray.from_number(1.9999999999)) == 1

    def test_should_cast_to_float(self):
        assert float(Ray.from_number(-4.5)) == -4.5
        assert float(Ray.from_number(0.99)) == 0.99
        assert float(Ray.from_number(1)) == 1.0
        assert float(Ray.from_number(1.0)) == 1.0
        assert float(Ray.from_number(1.5)) == 1.5
        assert float(Ray.from_number(1.9999999999)) == 1.9999999999

    def test_should_be_hashable(self):
        assert is_hashable(Ray(123))

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

    def test_round(self):
        assert round(Ray.from_number(123.4567), 2) == Ray.from_number(123.46)
        assert round(Ray.from_number(123.4567), 0) == Ray.from_number(123.0)
        assert round(Ray.from_number(123.4567), -2) == Ray.from_number(100.0)


class TestRad:
    def test_should_support_negative_values(self):
        Rad(-1)

    def test_should_support_values_greater_than_uint256(self):
        Rad(2**256)
        Rad(2**256 + 1)
        Rad(2**512)

    def test_should_instantiate_from_a_rad(self):
        assert Rad(Rad(1)) == Rad(1)

    def test_should_instantiate_from_a_wad(self):
        assert Rad(Wad(10000000000000000000)) == Rad.from_number(10)

    def test_should_instantiate_from_a_ray(self):
        assert Rad(Ray.from_number(10)) == Rad.from_number(10)

    def test_should_instantiate_from_an_int(self):
        assert Rad(10).value == 10

    def test_should_fail_to_instantiate_from_a_float(self):
        with pytest.raises(ArithmeticError):
            assert Rad(10.5)

    def test_should_format_to_string_nicely(self):
        assert str(Rad(1)) == "0.000000000000000000000000000000000000000000001"
        assert str(Rad(500000000000000000000000000000000000000000000)) == "0.500000000000000000000000000000000000000000000"
        assert str(Rad(1500000000000000000000000000000000000000000000)) == "1.500000000000000000000000000000000000000000000"
        assert str(Rad(-1500000000000000000000000000000000000000000000)) == "-1.500000000000000000000000000000000000000000000"
        assert str(Rad(-500000000000000000000000000000000000000000000)) == "-0.500000000000000000000000000000000000000000000"
        assert str(Rad(-1)) == "-0.000000000000000000000000000000000000000000001"

    def test_should_have_nice_printable_representation(self):
        for ray in [Rad(1), Rad(100), Rad.from_number(2.5), Rad(-1)]:
            assert repr(ray) == f"Rad({ray.value})"

    def test_add(self):
        assert Rad(1) + Rad(2) == Rad(3)

    def test_add_should_not_work_with_wads(self):
        with pytest.raises(ArithmeticError):
            Rad(1) + Wad(2)

    def test_add_should_not_work_with_rays(self):
        with pytest.raises(ArithmeticError):
            Rad(1) + Ray(2)

    def test_add_should_not_work_with_ints(self):
        with pytest.raises(ArithmeticError):
            Rad(1) + 2

    def test_subtract(self):
        assert Rad(10) - Rad(2) == Rad(8)
        assert Rad(1) - Rad(2) == Rad(-1)

    def test_subtract_should_not_work_with_wads(self):
        with pytest.raises(ArithmeticError):
            Rad(10) - Wad(2)

    def test_subtract_should_not_work_with_rays(self):
        with pytest.raises(ArithmeticError):
            Rad(10) - Ray(2)

    def test_multiply(self):
        assert Rad.from_number(2) * Rad.from_number(3) == Rad.from_number(6)
        assert Rad.from_number(2) * Rad(3) == Rad(6)
        assert Rad.from_number(2.5) * Rad(3) == Rad(7)
        assert Rad.from_number(2.99999) * Rad(3) == Rad(8)

    def test_multiply_by_wad(self):
        assert Rad.from_number(2) * Wad.from_number(3) == Rad.from_number(6)
        assert Rad.from_number(2) * Wad(3) == Rad(6000000000000000000000000000)
        assert Rad(2) * Wad(3) == Rad(0)
        assert Rad(2) * Wad(999999999999999999) == Rad(1)
        assert Rad(2) * Wad(1000000000000000000) == Rad(2)

    def test_multiply_by_ray(self):
        assert Rad.from_number(2) * Ray.from_number(3) == Rad.from_number(6)
        assert Rad.from_number(2) * Ray(3) == Rad(6000000000000000000)
        assert Rad(2) * Ray(3) == Rad(0)
        assert Rad(2) * Ray(999999999999999999999999999) == Rad(1)
        assert Rad(2) * Ray(1000000000000000000000000000) == Rad(2)

    def test_multiply_by_int(self):
        assert Rad.from_number(2) * 3 == Rad.from_number(6)
        assert Rad.from_number(2) * 1 == Rad.from_number(2)

    def test_should_fail_to_multiply_by_float(self):
        with pytest.raises(ArithmeticError):
            Rad(2) * 3.0

    def test_divide(self):
        assert Rad.from_number(4) / Rad.from_number(2) == Rad.from_number(2)
        assert Rad(4) / Rad.from_number(2) == Rad(2)
        assert Rad(3) / Rad.from_number(2) == Rad(1)
        assert Rad(39) / Rad.from_number(20) == Rad(1)
        assert Rad(40) / Rad.from_number(20) == Rad(2)
        assert Rad.from_number(0.2) / Rad.from_number(0.1) == Rad.from_number(2)

    def test_should_fail_to_divide_by_wads(self):
        with pytest.raises(ArithmeticError):
            Rad(4) / Wad(2)

    def test_should_fail_to_divide_by_rays(self):
        with pytest.raises(ArithmeticError):
            Rad(4) / Ray(2)

    def test_should_fail_to_divide_by_ints(self):
        with pytest.raises(ArithmeticError):
            Rad(4) / 2

    def test_should_support_abs(self):
        assert abs(Rad(1000)) == Rad(1000)
        assert abs(Rad(0)) == Rad(0)
        assert abs(Rad(-1000)) == Rad(1000)

    def test_should_compare_rays_with_each_other(self):
        assert Rad(1000) == Rad(1000)
        assert Rad(1000) != Rad(999)
        assert Rad(1000) > Rad(999)
        assert Rad(999) < Rad(1000)
        assert Rad(999) <= Rad(1000)
        assert Rad(1000) <= Rad(1000)
        assert Rad(1000) >= Rad(1000)
        assert Rad(1000) >= Rad(999)

    def test_should_reject_comparison_with_wads(self):
        with pytest.raises(ArithmeticError):
            assert Rad(1000) == Wad(1000)
        with pytest.raises(ArithmeticError):
            assert Rad(1000) != Wad(999)
        with pytest.raises(ArithmeticError):
            assert Rad(1000) > Wad(999)
        with pytest.raises(ArithmeticError):
            assert Rad(999) < Wad(1000)
        with pytest.raises(ArithmeticError):
            assert Rad(999) <= Wad(1000)
        with pytest.raises(ArithmeticError):
            assert Rad(1000) <= Wad(1000)
        with pytest.raises(ArithmeticError):
            assert Rad(1000) >= Wad(1000)
        with pytest.raises(ArithmeticError):
            assert Rad(1000) >= Wad(999)

    def test_should_reject_comparison_with_rays(self):
        with pytest.raises(ArithmeticError):
            assert Rad(1000) == Ray(1000)
        with pytest.raises(ArithmeticError):
            assert Rad(1000) != Ray(999)
        with pytest.raises(ArithmeticError):
            assert Rad(1000) > Ray(999)
        with pytest.raises(ArithmeticError):
            assert Rad(999) < Ray(1000)
        with pytest.raises(ArithmeticError):
            assert Rad(999) <= Ray(1000)
        with pytest.raises(ArithmeticError):
            assert Rad(1000) <= Ray(1000)
        with pytest.raises(ArithmeticError):
            assert Rad(1000) >= Ray(1000)
        with pytest.raises(ArithmeticError):
            assert Rad(1000) >= Ray(999)

    def test_should_reject_comparison_with_ints(self):
        with pytest.raises(ArithmeticError):
            assert Rad(1000) == 100
        with pytest.raises(ArithmeticError):
            assert Rad(1000) != 999
        with pytest.raises(ArithmeticError):
            assert Rad(1000) > 999
        with pytest.raises(ArithmeticError):
            assert Rad(999) < 1000
        with pytest.raises(ArithmeticError):
            assert Rad(999) <= 1000
        with pytest.raises(ArithmeticError):
            assert Rad(1000) <= 1000
        with pytest.raises(ArithmeticError):
            assert Rad(1000) >= 1000
        with pytest.raises(ArithmeticError):
            assert Rad(1000) >= 999

    def test_should_cast_to_int(self):
        assert int(Rad.from_number(-4.5)) == -4
        assert int(Rad.from_number(0.99)) == 0
        assert int(Rad.from_number(1)) == 1
        assert int(Rad.from_number(1.0)) == 1
        assert int(Rad.from_number(1.5)) == 1
        assert int(Rad.from_number(1.9999999999)) == 1

    def test_should_cast_to_float(self):
        assert float(Rad.from_number(-4.5)) == -4.5
        assert float(Rad.from_number(0.99)) == 0.99
        assert float(Rad.from_number(1)) == 1.0
        assert float(Rad.from_number(1.0)) == 1.0
        assert float(Rad.from_number(1.5)) == 1.5
        assert float(Rad.from_number(1.9999999999)) == 1.9999999999

    def test_should_be_hashable(self):
        assert is_hashable(Rad(123))

    def test_min_value(self):
        assert Rad.min(Rad(10), Rad(20)) == Rad(10)
        assert Rad.min(Rad(25), Rad(15)) == Rad(15)
        assert Rad.min(Rad(25), Rad(15), Rad(5)) == Rad(5)

    def test_min_value_should_reject_comparison_with_wads(self):
        with pytest.raises(ArithmeticError):
            Rad.min(Rad(10), Wad(20))
        with pytest.raises(ArithmeticError):
            Rad.min(Wad(25), Rad(15))

    def test_min_value_should_reject_comparison_with_rays(self):
        with pytest.raises(ArithmeticError):
            Rad.min(Rad(10), Ray(20))
        with pytest.raises(ArithmeticError):
            Rad.min(Ray(25), Rad(15))

    def test_min_value_should_reject_comparison_with_ints(self):
        with pytest.raises(ArithmeticError):
            Rad.min(Rad(10), 20)
        with pytest.raises(ArithmeticError):
            Rad.min(20, Rad(10))

    def test_max_value(self):
        assert Rad.max(Rad(10), Rad(20)) == Rad(20)
        assert Rad.max(Rad(25), Rad(15)) == Rad(25)
        assert Rad.max(Rad(25), Rad(15), Rad(40)) == Rad(40)

    def test_max_value_should_reject_comparison_with_wads(self):
        with pytest.raises(ArithmeticError):
            Rad.max(Rad(10), Wad(20))
        with pytest.raises(ArithmeticError):
            Rad.max(Rad(25), Wad(15))

    def test_max_value_should_reject_comparison_with_rays(self):
        with pytest.raises(ArithmeticError):
            Rad.max(Rad(10), Ray(20))
        with pytest.raises(ArithmeticError):
            Rad.max(Rad(25), Ray(15))

    def test_max_value_should_reject_comparison_with_ints(self):
        with pytest.raises(ArithmeticError):
            Rad.max(Rad(10), 20)
        with pytest.raises(ArithmeticError):
            Rad.max(15, Rad(25))

    def test_round(self):
        assert round(Rad.from_number(123.4567), 2) == Rad.from_number(123.46)
        assert round(Rad.from_number(123.4567), 0) == Rad.from_number(123.0)
        assert round(Rad.from_number(123.4567), -2) == Rad.from_number(100.0)
