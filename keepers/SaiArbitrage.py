
from keepers.arbitrage.Conversion import Conversion
from keepers.arbitrage.OpportunityFinder import OpportunityFinder


def rates():
    return [
        Conversion("USD", "JPY", "91.7074025"),
        Conversion("JPY", "EUR", "0.0083835"), #this
        Conversion("BTC", "USD", "109.1976214"),
        Conversion("JPY", "BTC", "0.0000896"),
        Conversion("USD", "EUR", "0.6962706"),
        Conversion("EUR", "USD", "1.4047063"),
        Conversion("EUR", "JPY", "143.9234472"), #this
        Conversion("JPY", "USD", "0.0107770"),
        Conversion("EUR", "BTC", "0.0122985"),
        Conversion("BTC", "JPY", "11178.1471392"),
        Conversion("BTC", "EUR", "80.5469380"),
        Conversion("USD", "BTC", "0.0074307"),

        # join/exit on the Tub
        # unlimited, the only limit is the amount of tokens we have
        # rate is Tub.per()
        Conversion("ETH", "SKR", "1", 0.6, "join"),
        Conversion("SKR", "ETH", "1", 0.6, "exit"),

        # take on the Lpc
        # limited, depends on how many tokens in the pool, but we can check it
        # rate is Lpc.tag() or 1/Lpc.tag(), depending on the direction
        Conversion("ETH", "SAI", "362.830", 0.6, "take-SAI"),
        Conversion("SAI", "ETH", str(1/float("362.830")), 0.6, "take-ETH"),

        # woe in the Tub
        # limited, depends on how much woe in the Tub (after "mending")
        # rate is 1/Tub.tag()
        Conversion("SAI", "SKR", str(float(1/float("362.830"))), 0.6, "bust"), #real data ["0.002756111677645"] []
        # Conversion("SAI", "SKR", "0.0083835", 0.6, "bust"), #fake data

        # joy in the Tub
        # limited, depends on how much joy in the Tub (after "mending")
        # rate is Tub.tag()
        # Conversion("SKR", "SAI", "362.830", 0.6, "boom"),

        # plus all the orders from Oasis
        Conversion("SKR", "SAI", "363.830", 0.6, "oasis-order"), #real data
        # Conversion("SKR", "SAI", "123.9234472", 0.6, "oasis-order"), #fake data
    ]

opportunities = OpportunityFinder(conversions=rates()).opportunities('SAI')
print(opportunities)
