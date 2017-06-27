import unittest

from api.Ray import Ray
from api.Wad import Wad
from keepers.arbitrage.Conversion import Conversion
from keepers.arbitrage.Opportunity import Opportunity


class TestOpportunity(unittest.TestCase):

    def setUp(self):
        pass

    def test_should_calculate_total_rate(self):
        # given
        conversion1 = Conversion('ABC', 'DEF', Ray.from_number(1.01), Wad.from_number(1), Wad.from_number(100), 'met')
        conversion2 = Conversion('DEF', 'ABC', Ray.from_number(1.02), Wad.from_number(1), Wad.from_number(100), 'met')
        opportunity = Opportunity([conversion1, conversion2])

        # except
        self.assertEqual(Ray.from_number(1.0302), opportunity.total_rate())


if __name__ == '__main__':
    unittest.main()
