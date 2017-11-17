# Maker Keeper Framework

Reference Maker Keeper Framework.

[![Build Status](https://travis-ci.org/makerdao/keeper.svg?branch=master)](https://travis-ci.org/makerdao/keeper)
[![codecov](https://codecov.io/gh/makerdao/keeper/branch/master/graph/badge.svg)](https://codecov.io/gh/makerdao/keeper)
[![Code Climate](https://codeclimate.com/github/makerdao/keeper/badges/gpa.svg)](https://codeclimate.com/github/makerdao/keeper)
[![Issue Count](https://codeclimate.com/github/makerdao/keeper/badges/issue_count.svg)](https://codeclimate.com/github/makerdao/keeper)

<https://chat.makerdao.com/channel/keeper>

## Introduction

The _SAI Stablecoin System_, as well as the _DAI Stablecoin System_ in the future,
both incentivize external agents, often called _keepers_, to automate certain operations
around the Ethereum blockchain.

This project contains a set of reference keepers, which can either be run directly
by profit-seeking parties, or can be used by them as a foundation for building
their own, more sophisticated keepers.

As a part of the reference keeper implementation, an API around most of the
_SAI Stablecoin System_ contracts has been created. It can be used not only by
keepers, but may also be found useful by authors of some other, unrelated utilities
aiming to interact with these contracts.

## Disclaimer

This set of reference keepers is provided for demonstration purposes only. If you,
by any chance, want to run them on the production network or provide them
with any real money or tokens, you do it on your own responsibility only.

As stated in the _GNU Affero General Public License_:

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

## Installation

This project uses *Python 3.6.2*.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/makerdao/keeper.git
pip3 install -r requirements.txt
```

### Installation of `etherdelta-socket`

The EtherDelta keeper utilizes `etherdelta-socket` (in the `utils` directory) to place orders using _socket.io_.
In order to use it, a node installation must be present and `npm install` needs to be run in the
`utils/etherdelta-socket` folder.

### Installation of `setzer`

The market maker keepers use `setzer` in order to access price feeds like GDAX, Kraken etc. In order
for it to work correctly, `setzer` and its dependencies must be installed and available to the keepers.
Please see https://github.com/makerdao/setzer.

Without `setzer` installed, only the default price feed (provided by `Tub`) will be available.

### Known macOS issues

In order for the Python requirements to install correctly on _macOS_, please install
`openssl`, `libtool` and `pkg-config` using [Homebrew](https://brew.sh/):
```
brew install openssl libtool pkg-config
```

and set the `LDFLAGS` environment variable before you run `pip3 install -r requirements.txt`:
```
export LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" 
```

## Running keepers

An individual script in the `bin` directory is present for each keeper. For example, `keeper-sai-bite`
can be run with:
```bash
bin/keeper-sai-bite --eth-from 0x0101010101010101010101010101010101010101
```

### Restarting dying keepers

As keepers tend to die at times, in any serious environment they should be run by a tool
which can restart them if they fail. It could be _systemd_, but if you don't want to set it up,
a simple `bin/run-forever` script has been provided. Its job is to simply restart the
specified program as long as it's return code is non-zero.

For example you could run the same `keeper-sai-bite` keeper like that:
```bash
bin/run-forever bin/keeper-sai-bite --eth-from 0x0101010101010101010101010101010101010101
```
so it gets automatically restarted every time it fails.

### Individual keeper accounts

**It is advised to run each keeper on their own Ethereum account**

### Unlocking accounts

Keepers will fail to start if the Ethereum accounts they are configured to operate on are not unlocked.
This post <https://ethereum.stackexchange.com/questions/15349/parity-unlock-multiple-accounts-at-startup/15351#15351>
describes how to unlock multiple accounts in Parity on startup.

## Reference keepers

This sections lists and briefly describes a set of reference keepers present in this project.

### `keeper-sai-bite`

SAI keeper to bite undercollateralized cups.

This keeper constantly looks for unsafe cups and bites them the moment they become
unsafe. Ultimately, it should take into account the profit it can make by processing
the resulting collateral via `bust` and only waste gas on `bite` if it can make it up
by subsequent arbitrage. For now, it is a dumb keeper that just bites every cup
that can be bitten.

Usage:
```
usage: keeper-sai-bite [-h] [--rpc-host RPC_HOST] [--rpc-port RPC_PORT]
                       --eth-from ETH_FROM [--gas-price GAS_PRICE]
                       [--initial-gas-price INITIAL_GAS_PRICE]
                       [--increase-gas-price-by INCREASE_GAS_PRICE_BY]
                       [--increase-gas-price-every INCREASE_GAS_PRICE_EVERY]
                       [--debug] [--trace]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --eth-from ETH_FROM   Ethereum account from which to send transactions
  --gas-price GAS_PRICE
                        Static gas pricing: Gas price in Wei
  --initial-gas-price INITIAL_GAS_PRICE
                        Increasing gas pricing: Initial gas price in Wei
  --increase-gas-price-by INCREASE_GAS_PRICE_BY
                        Increasing gas pricing: Gas price increase in Wei
  --increase-gas-price-every INCREASE_GAS_PRICE_EVERY
                        Increasing gas pricing: Gas price increase interval in
                        seconds
  --debug               Enable debug output
  --trace               Enable trace output
```

### `keeper-sai-arbitrage`

SAI keeper to arbitrage on OasisDEX, `join`, `exit`, `boom` and `bust`.

Keeper constantly looks for profitable enough arbitrage opportunities
and executes them the moment they become available. It can make profit on:
* taking orders on OasisDEX (on SAI/SKR, SAI/W-ETH and SKR/W-ETH pairs),
* calling `join` and `exit` to exchange between W-ETH and SKR,
* calling `boom` and `bust` to exchange between SAI and SKR.

Opportunities discovered by the keeper are sequences of token exchanges
executed using methods listed above. An opportunity can consist of two
or three steps, technically it could be more but practically it will never
be more than three.

Steps can be executed sequentially (each one as a separate Etheruem
transaction, checking if one has been successful before executing the next
one) or in one ago. The latter method requires a `TxManager` contract deployed,
its address has to be passed as the `--tx-manager` argument. Also the `TxManager`
contract has to be owned by the account the keeper operates from.

You can find the source code of the `TxManager` here:
<https://github.com/reverendus/tx-manager>.

The base token of this keeper is SAI i.e. all arbitrage opportunities will
start with some amount of SAI, exchange it to some other token(s) and then exchange
back to SAI, aiming to end up with more SAI than it started with. The keeper is aware
of gas costs and takes a rough estimate of these costs while calculating arbitrage
profitability.

Usage:
```
usage: keeper-sai-arbitrage [-h] [--rpc-host RPC_HOST] [--rpc-port RPC_PORT]
                            --eth-from ETH_FROM [--gas-price GAS_PRICE]
                            [--initial-gas-price INITIAL_GAS_PRICE]
                            [--increase-gas-price-by INCREASE_GAS_PRICE_BY]
                            [--increase-gas-price-every INCREASE_GAS_PRICE_EVERY]
                            [--debug] [--trace] --base-token BASE_TOKEN
                            --min-profit MIN_PROFIT --max-engagement
                            MAX_ENGAGEMENT [--max-errors MAX_ERRORS]
                            [--tx-manager TX_MANAGER]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --eth-from ETH_FROM   Ethereum account from which to send transactions
  --gas-price GAS_PRICE
                        Static gas pricing: Gas price in Wei
  --initial-gas-price INITIAL_GAS_PRICE
                        Increasing gas pricing: Initial gas price in Wei
  --increase-gas-price-by INCREASE_GAS_PRICE_BY
                        Increasing gas pricing: Gas price increase in Wei
  --increase-gas-price-every INCREASE_GAS_PRICE_EVERY
                        Increasing gas pricing: Gas price increase interval in
                        seconds
  --debug               Enable debug output
  --trace               Enable trace output
  --base-token BASE_TOKEN
                        The token all arbitrage sequences will start and end
                        with
  --min-profit MIN_PROFIT
                        Minimum profit (in base token) from one arbitrage
                        operation
  --max-engagement MAX_ENGAGEMENT
                        Maximum engagement (in base token) in one arbitrage
                        operation
  --max-errors MAX_ERRORS
                        Maximum number of allowed errors before the keeper
                        terminates (default: 100)
  --tx-manager TX_MANAGER
                        Address of the TxManager to use for multi-step
                        arbitrage
```

### `keeper-sai-top-up`

SAI keeper to top-up cups before they reach the liquidation ratio.

Kepper constantly monitors cups owned by the `--eth-from` account. If the
collateralization ratio falls under `mat` + `--min-margin`, the cup will get
topped-up up to `mat` + `--top-up-margin`.

Cups owned by other accounts are ignored.

Usage:
```
usage: keeper-sai-top-up [-h] [--rpc-host RPC_HOST] [--rpc-port RPC_PORT]
                         --eth-from ETH_FROM [--gas-price GAS_PRICE]
                         [--initial-gas-price INITIAL_GAS_PRICE]
                         [--increase-gas-price-by INCREASE_GAS_PRICE_BY]
                         [--increase-gas-price-every INCREASE_GAS_PRICE_EVERY]
                         [--debug] [--trace] [--min-margin MIN_MARGIN]
                         [--top-up-margin TOP_UP_MARGIN]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --eth-from ETH_FROM   Ethereum account from which to send transactions
  --gas-price GAS_PRICE
                        Static gas pricing: Gas price in Wei
  --initial-gas-price INITIAL_GAS_PRICE
                        Increasing gas pricing: Initial gas price in Wei
  --increase-gas-price-by INCREASE_GAS_PRICE_BY
                        Increasing gas pricing: Gas price increase in Wei
  --increase-gas-price-every INCREASE_GAS_PRICE_EVERY
                        Increasing gas pricing: Gas price increase interval in
                        seconds
  --debug               Enable debug output
  --trace               Enable trace output
  --min-margin MIN_MARGIN
                        Margin between the liquidation ratio and the top-up
                        threshold
  --top-up-margin TOP_UP_MARGIN
                        Margin between the liquidation ratio and the top-up
                        target
```

### `keeper-sai-maker-otc`

SAI keeper to act as a market maker on OasisDEX, on the W-ETH/SAI pair.

Keeper continuously monitors and adjusts its positions in order to act as a market maker.
It maintains buy and sell orders in multiple bands at the same time. In each buy band,
it aims to have open SAI sell orders for at least `minSaiAmount`. In each sell band
it aims to have open WETH sell orders for at least `minWEthAmount`. In both cases,
it will ensure the price of open orders stays within the <minMargin,maxMargin> range
from the current SAI/W-ETH price.

When started, the keeper places orders for the average amounts (`avgSaiAmount`
and `avgWEthAmount`) in each band and uses `avgMargin` to calculate the order price.

As long as the price of orders stays within the band (i.e. is in the <minMargin,maxMargin>
range from the current SAI/W-ETH price, which is of course constantly moving), the keeper
keeps them open. If they leave the band, they either enter another adjacent band
or fall outside all bands. In case of the latter, they get immediately cancelled. In case of
the former, the keeper can keep these orders open as long as their amount is within the
<minSaiAmount,maxSaiAmount> (for buy bands) or <minWEthAmount,maxWEthAmount> (for sell bands)
ranges for the band they just entered. If it is above the maximum, all open orders will get
cancelled and a new one will be created (for the `avgSaiAmount` / `avgWEthAmount`). If it is below
the minimum, a new order gets created for the remaining amount so the total amount of orders
in this band is equal to `avgSaiAmount` or `avgWEthAmount`.

The same thing will happen if the total amount of open orders in a band falls below either
`minSaiAmount` or `minWEthAmount` as a result of other market participants taking these orders.
In this case also a new order gets created for the remaining amount so the total
amount of orders in this band is equal to `avgSaiAmount` / `avgWEthAmount`.

This keeper will constantly use gas to move orders as the SAI/GEM price changes. Gas usage
can be limited by setting the margin and amount ranges wide enough and also by making
sure that bands are always adjacent to each other and that their <min,max> amount ranges
overlap.

Usage:
```
usage: keeper-sai-maker-otc [-h] [--rpc-host RPC_HOST] [--rpc-port RPC_PORT]
                            --eth-from ETH_FROM [--gas-price GAS_PRICE]
                            [--initial-gas-price INITIAL_GAS_PRICE]
                            [--increase-gas-price-by INCREASE_GAS_PRICE_BY]
                            [--increase-gas-price-every INCREASE_GAS_PRICE_EVERY]
                            [--debug] [--trace] --config CONFIG
                            [--round-places ROUND_PLACES]

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --eth-from ETH_FROM   Ethereum account from which to send transactions
  --gas-price GAS_PRICE
                        Static gas pricing: Gas price in Wei
  --initial-gas-price INITIAL_GAS_PRICE
                        Increasing gas pricing: Initial gas price in Wei
  --increase-gas-price-by INCREASE_GAS_PRICE_BY
                        Increasing gas pricing: Gas price increase in Wei
  --increase-gas-price-every INCREASE_GAS_PRICE_EVERY
                        Increasing gas pricing: Gas price increase interval in
                        seconds
  --debug               Enable debug output
  --trace               Enable trace output
  --config CONFIG       Buy/sell bands configuration file
  --round-places ROUND_PLACES
                        Number of decimal places to round order prices to
                        (default=2)
```

Sample buy/sell bands configuration file:

```json
{
    "buyBands": [
        {
            "minMargin": 0.005,
            "avgMargin": 0.01,
            "maxMargin": 0.02,
            "minSaiAmount": 20.0,
            "avgSaiAmount": 30.0,
            "maxSaiAmount": 40.0,
            "dustCutoff": 0.0
        },
        {
            "minMargin": 0.02,
            "avgMargin": 0.025,
            "maxMargin": 0.03,
            "minSaiAmount": 40.0,
            "avgSaiAmount": 60.0,
            "maxSaiAmount": 80.0,
            "dustCutoff": 0.0
        }
    ],
    "sellBands": [
        {
            "minMargin": 0.005,
            "avgMargin": 0.01,
            "maxMargin": 0.02,
            "minWEthAmount": 2.5,
            "avgWEthAmount": 5.0,
            "maxWEthAmount": 7.5,
            "dustCutoff": 0.0
        },
        {
            "minMargin": 0.02,
            "avgMargin": 0.025,
            "maxMargin": 0.03,
            "minWEthAmount": 4.0,
            "avgWEthAmount": 6.0,
            "maxWEthAmount": 8.0,
            "dustCutoff": 0.0
        }
    ]
}
```

### `keeper-sai-maker-etherdelta`

SAI keeper to act as a market maker on EtherDelta, on the ETH/SAI pair.

Due to limitations of EtherDelta, **the development of this keeper has been
discontinued**. It works most of the time, but due to the fact that EtherDelta
was a bit unpredictable in terms of placing orders at the time this keeper
was developed, we abandoned it and decided to stick to SaiMakerOtc for now.

## Testing

Maker Keeper Framework uses [pytest](https://docs.pytest.org/en/latest/) for unit testing.

In order to be able to run tests, please install development dependencies first by executing:
```
pip3 install -r requirements-dev.txt
```

You can then run all tests with:
```
pytest
```

## APIs for smart contracts

In order simplify keeper development, a set of APIs has been developed around the core contracts
of the _SAI Stablecoin_ ecosystem. The current version provides APIs around:
* `ERC20Token`,
* `Tub`, `Tap`, `Top` and `Lpc` (<https://github.com/makerdao/sai>),
* `SimpleMarket`, `ExpiringMarket` and `MatchingMarket` (<https://github.com/makerdao/maker-otc>),
* `TxManager` (<https://github.com/reverendus/tx-manager>),
* `DSGuard` (<https://github.com/dapphub/ds-guard>),
* `DSProxy` (<https://github.com/dapphub/ds-proxy>),
* `DSRoles` (<https://github.com/dapphub/ds-roles>),
* `DSToken` (<https://github.com/dapphub/ds-token>),
* `DSEthToken` (<https://github.com/dapphub/ds-eth-token>),
* `DSValue` (<https://github.com/dapphub/ds-value>),
* `DSVault` (<https://github.com/dapphub/ds-vault>).

In addition to that, there are draft interfaces to:
* `EtherDelta` (<https://github.com/etherdelta/etherdelta.github.io>).

There is also a _Setzer_ class which provides a simple interface to the `setzer` commandline
tool (<https://github.com/makerdao/setzer>).

You can find the full documentation of the APIs here: http://maker-keeper-docs.surge.sh.

**Beware!** This is the first version of the APIs and they will definitely change
and/or evolve in the future.

## Code samples

Below you can find some code snippets demonstrating how the API can be used both for developing
your own keepers and for creating some other utilities interacting with the _SAI Stablecoin_
ecosystem contracts.

### Token transfer

This snippet demonstrates how to transfer some SAI from our default address. The SAI token address
is discovered by querying the `Tub`, so all we need as a `Tub` address:

```python
from web3 import HTTPProvider, Web3

from keeper.api import Address
from keeper.api.token import ERC20Token
from keeper.api.numeric import Wad
from keeper.api.sai import Tub


web3 = Web3(HTTPProvider(endpoint_uri="http://localhost:8545"))

tub = Tub(web3=web3, address=Address('0xb7ae5ccabd002b5eebafe6a8fad5499394f67980'))
sai = ERC20Token(web3=web3, address=tub.sai())

sai.transfer(address=Address('0x0000000000111111111100000000001111111111'),
             value=Wad.from_number(10)).transact()
``` 

### Updating a DSValue

This snippet demonstrates how to update a `DSValue` with the ETH/USD rate pulled from _CryptoCompare_: 

```python
import json
import urllib.request

from web3 import HTTPProvider, Web3

from keeper.api import Address
from keeper.api.feed import DSValue
from keeper.api.numeric import Wad


def cryptocompare_rate() -> Wad:
    with urllib.request.urlopen("https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD") as url:
        data = json.loads(url.read().decode())
        return Wad.from_number(data['USD'])


web3 = Web3(HTTPProvider(endpoint_uri="http://localhost:8545"))

dsvalue = DSValue(web3=web3, address=Address('0x038b3d8288df582d57db9be2106a27be796b0daf'))
dsvalue.poke_with_int(cryptocompare_rate().value).transact()
```

### SAI introspection

This snippet demonstrates how to fetch data from `Tub` and `Tap` contracts:

```python
from web3 import HTTPProvider, Web3

from keeper.api import Address
from keeper.api.token import ERC20Token
from keeper.api.numeric import Ray
from keeper.api.sai import Tub, Tap


web3 = Web3(HTTPProvider(endpoint_uri="http://localhost:8545"))

tub = Tub(web3=web3, address=Address('0xb7ae5ccabd002b5eebafe6a8fad5499394f67980'))
tap = Tap(web3=web3, address=Address('0xb9e0a196d2150a6393713e09bd79a0d39293ec13'))
sai = ERC20Token(web3=web3, address=tub.sai())
skr = ERC20Token(web3=web3, address=tub.skr())
gem = ERC20Token(web3=web3, address=tub.gem())

print(f"")
print(f"Token summary")
print(f"-------------")
print(f"SAI total supply       : {sai.total_supply()} SAI")
print(f"SKR total supply       : {skr.total_supply()} SKR")
print(f"GEM total supply       : {gem.total_supply()} GEM")
print(f"")
print(f"Collateral summary")
print(f"------------------")
print(f"GEM collateral         : {tub.pie()} GEM")
print(f"SKR collateral         : {tub.air()} SKR")
print(f"SKR pending liquidation: {tap.fog()} SKR")
print(f"")
print(f"Debt summary")
print(f"------------")
print(f"Debt ceiling           : {tub.hat()} SAI")
print(f"Good debt              : {tub.ice()} SAI")
print(f"Bad debt               : {tap.woe()} SAI")
print(f"Surplus                : {tap.joy()} SAI")
print(f"")
print(f"Feed summary")
print(f"------------")
print(f"REF per GEM feed       : {tub.pip()}")
print(f"REF per SKR price      : {tub.tag()}")
print(f"GEM per SKR price      : {tub.per()}")
print(f"")
print(f"Tub parameters")
print(f"--------------")
print(f"Liquidation ratio      : {tub.mat()*100} %")
print(f"Liquidation penalty    : {tub.axe()*100 - Ray.from_number(100)} %")
print(f"Stability fee          : {tub.tax()} %")
print(f"Holder fee             : {tub.way()} %")
print(f"")
print(f"All cups")
print(f"--------")
for cup_id in range(1, tub.cupi()+1):
    cup = tub.cups(cup_id)
    print(f"Cup #{cup_id}, lad={cup.lad}, ink={cup.ink} SKR, tab={tub.tab(cup_id)} SAI, safe={tub.safe(cup_id)}")
```

### Asynchronous invocation of Ethereum transactions

This snippet demonstrates how multiple token transfers can be executed asynchronously:

```python
from web3 import HTTPProvider
from web3 import Web3

from keeper.api import Address, Wad, synchronize
from keeper.api.sai import Tub
from keeper.api.token import ERC20Token


web3 = Web3(HTTPProvider(endpoint_uri="http://localhost:8545"))

tub = Tub(web3=web3, address=Address('0xb7ae5ccabd002b5eebafe6a8fad5499394f67980'))
sai = ERC20Token(web3=web3, address=tub.sai())
skr = ERC20Token(web3=web3, address=tub.skr())

synchronize([sai.transfer(Address('0x0101010101020202020203030303030404040404'), Wad.from_number(1.5)).transact_async(),
             skr.transfer(Address('0x0303030303040404040405050505050606060606'), Wad.from_number(2.5)).transact_async()])
```

### Multiple invocations in one Ethereum transaction

This snippet demonstrates how multiple token transfers can be executed in one Ethereum transaction.
A `TxManager` instance has to be deployed and owned by the caller.

```python
from web3 import HTTPProvider
from web3 import Web3

from keeper.api import Address, Wad
from keeper.api.approval import directly
from keeper.api.sai import Tub
from keeper.api.token import ERC20Token
from keeper.api.transact import TxManager


web3 = Web3(HTTPProvider(endpoint_uri="http://localhost:8545"))

tub = Tub(web3=web3, address=Address('0xb7ae5ccabd002b5eebafe6a8fad5499394f67980'))
sai = ERC20Token(web3=web3, address=tub.sai())
skr = ERC20Token(web3=web3, address=tub.skr())

tx = TxManager(web3=web3, address=Address('0x57bFE16ae8fcDbD46eDa9786B2eC1067cd7A8f48'))
tx.approve([sai, skr], directly())

tx.execute([sai.address, skr.address],
           [sai.transfer(Address('0x0101010101020202020203030303030404040404'), Wad.from_number(1.5)).invocation(),
            skr.transfer(Address('0x0303030303040404040405050505050606060606'), Wad.from_number(2.5)).invocation()]).transact()
```

## License

See [COPYING](https://github.com/makerdao/keeper/blob/master/COPYING) file.
