# Based on https://raw.githubusercontent.com/rosshochwert/arbitrage/master/arbitrage.py

import math


class Conversion:
    def __init__(self, from_currency, to_currency, rate, fee_in_usd=None, method=None):
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.rate = rate
        self.rate_for_graph = float(-math.log(float(rate)))
        self.fee_in_usd = fee_in_usd
        self.method = method


def rates():
    return [
        # Conversion("USD", "JPY", "91.7074025"),
        # Conversion("JPY", "EUR", "0.0083835"), #this
        # Conversion("BTC", "USD", "109.1976214"),
        # Conversion("JPY", "BTC", "0.0000896"),
        # Conversion("USD", "EUR", "0.6962706"),
        # Conversion("EUR", "USD", "1.4047063"),
        # Conversion("EUR", "JPY", "143.9234472"), #this
        # Conversion("JPY", "USD", "0.0107770"),
        # Conversion("EUR", "BTC", "0.0122985"),
        # Conversion("BTC", "JPY", "11178.1471392"),
        # Conversion("BTC", "EUR", "80.5469380"),
        # Conversion("USD", "BTC", "0.0074307"),

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
        Conversion("SAI", "SKR", str(float(1/float("362.830"))), 0.6, "bust"), #real data ["0.002756111677645"] [str(float(1/float("362.830")))]
        # Conversion("SAI", "SKR", "0.0083835", 0.6, "bust"), #fake data

        # joy in the Tub
        # limited, depends on how much joy in the Tub (after "mending")
        # rate is Tub.tag()
        # Conversion("SKR", "SAI", "362.830", 0.6, "boom"),

        # plus all the orders from Oasis
        Conversion("SKR", "SAI", "365.830", 0.6, "oasis-order"), #real data
        # Conversion("SKR", "SAI", "123.9234472", 0.6, "oasis-order"), #fake data
    ]

def rates_to_graph(rates):
    graph = {}

    for entry in rates:
        from_rate = entry.from_currency
        to_rate = entry.to_currency
        if from_rate != to_rate:
            if from_rate not in graph:
                graph[from_rate] = {}
            graph[from_rate][to_rate] = entry.rate_for_graph
    return graph

# Step 1: For each node prepare the destination and predecessor
def initialize(graph, source):
    d = {} # Stands for destination
    p = {} # Stands for predecessor
    for node in graph:
        d[node] = float('Inf') # We start admiting that the rest of nodes are very very far
        p[node] = None
    d[source] = 0 # For the source we know how to reach
    return d, p

def relax(node, neighbour, graph, d, p):
    # If the distance between the node and the neighbour is lower than the one I have now
    if d[neighbour] > d[node] + graph[node][neighbour]:
        # Record this lower distance
        d[neighbour] = d[node] + graph[node][neighbour]
        p[neighbour] = node

def retrace_negative_loop(p, start):
    arbitrageLoop = [start]
    next_node = start
    while True:
        if next_node is None:
            return None
        next_node = p[next_node]
        if next_node not in arbitrageLoop:
            arbitrageLoop.append(next_node)
        else:
            arbitrageLoop.append(next_node)
            arbitrageLoop = arbitrageLoop[arbitrageLoop.index(next_node):]
            return arbitrageLoop


def bellman_ford(graph, source):
    d, p = initialize(graph, source)
    for i in range(len(graph)-1): #Run this until is converges
        for u in graph:
            for v in graph[u]: #For each neighbour of u
                relax(u, v, graph, d, p) #Lets relax it


    # Step 3: check for negative-weight cycles
    for u in graph:
        for v in graph[u]:
            if d[v] < d[u] + graph[u][v]:
                return retrace_negative_loop(p, source)
    return None

paths = []

graph = rates_to_graph(rates())

for key in graph:
    path = bellman_ford(graph, key)
    if path not in paths:
        if path is not None:
            paths.append(path)

for path in paths:
    if path is None:
        print("No opportunity here :(")
    else:
        money = 100
        rate_total = 1.0
        print("Starting with %(money)i in %(currency)s" % {"money":money,"currency":path[0]})

        for i,value in enumerate(path):
            if i+1 < len(path):
                start = path[i]
                end = path[i+1]
                rate = math.exp(-graph[start][end])
                money *= rate
                rate_total *= rate
                print("%(start)s to %(end)s at %(rate)f = %(money)f" % {"start":start,"end":end,"rate":rate,"money":money})
        if rate_total < 1.0:
            print("^^ this is not an arbitrage apportunity!!!")
    print("\n")
