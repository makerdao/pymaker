# Based on https://raw.githubusercontent.com/rosshochwert/arbitrage/master/arbitrage.py

import math


class Conversion:
    def __init__(self, from_currency, to_currency, rate):
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.rate = rate
        self.rate_for_graph = float(-math.log(float(rate)))


def rates():
    return [
        Conversion("USD", "JPY", "91.7074025"),
        Conversion("JPY", "EUR", "0.0083835"),
        Conversion("BTC", "USD", "109.1976214"),
        Conversion("JPY", "BTC", "0.0000896"),
        Conversion("USD", "EUR", "0.6962706"),
        Conversion("EUR", "USD", "1.4047063"),
        Conversion("EUR", "JPY", "143.9234472"),
        Conversion("JPY", "USD", "0.0107770"),
        Conversion("EUR", "BTC", "0.0122985"),
        Conversion("BTC", "JPY", "11178.1471392"),
        Conversion("BTC", "EUR", "80.5469380"),
        Conversion("USD", "BTC", "0.0074307"),
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
        d[neighbour]  = d[node] + graph[node][neighbour]
        p[neighbour] = node

def retrace_negative_loop(p, start):
    arbitrageLoop = [start]
    next_node = start
    while True:
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
                return(retrace_negative_loop(p, source))
    return None

paths = []

graph = rates_to_graph(rates())

for key in graph:
    path = bellman_ford(graph, key)
    if path not in paths and not None:
        paths.append(path)

for path in paths:
    if path == None:
        print("No opportunity here :(")
    else:
        money = 100
        print("Starting with %(money)i in %(currency)s" % {"money":money,"currency":path[0]})

        for i,value in enumerate(path):
            if i+1 < len(path):
                start = path[i]
                end = path[i+1]
                rate = math.exp(-graph[start][end])
                money *= rate
                print("%(start)s to %(end)s at %(rate)f = %(money)f" % {"start":start,"end":end,"rate":rate,"money":money})
    print("\n")
