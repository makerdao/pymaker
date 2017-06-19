
from keepers.arbitrage.Conversion import Conversion
from keepers.arbitrage.OpportunityFinder import OpportunityFinder


def rates():
    return [
        # join/exit on the Tub
        # unlimited, the only limit is the amount of tokens we have
        # rate is Tub.per()
        Conversion("ETH", "SKR", "1", 100, 0.6, "tub-join"),
        Conversion("SKR", "ETH", "1", 100, 0.6, "tub-exit"),

        # take on the Lpc
        # limited, depends on how many tokens in the pool, but we can check it
        # rate is Lpc.tag() or 1/Lpc.tag(), depending on the direction
        Conversion("ETH", "SAI", "362.830", 100, 0.6, "lpc-take-SAI"),
        Conversion("SAI", "ETH", str(1/float("362.830")), 100, 0.6, "lpc-take-ETH"),

        # woe in the Tub
        # limited, depends on how much woe in the Tub (after "mending")
        # rate is 1/Tub.tag()
        Conversion("SAI", "SKR", str(float(1/float("362.830"))), 100, 0.6, "tub-bust"), #real data ["0.002756111677645"] []

        # joy in the Tub
        # limited, depends on how much joy in the Tub (after "mending")
        # rate is Tub.tag()
        # Conversion("SKR", "SAI", "362.830", 0.6, "tub-boom"),

        # plus all the orders from Oasis
        Conversion("SKR", "SAI", "363.830", 100, 0.6, "oasis-takeOrder-121"), #real data
    ]

opportunities = OpportunityFinder(conversions=rates()).opportunities('SAI')
opportunities = filter(lambda opportunity: opportunity.total_rate() > 1.0, opportunities)
for opportunity in opportunities:
    print(repr(opportunity))
