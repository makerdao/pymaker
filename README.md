# Maker Keeper Framework

Reference Maker Keeper Framework.

[![Build Status](https://travis-ci.org/makerdao/keeper.svg?branch=master)](https://travis-ci.org/makerdao/keeper)
[![codecov](https://codecov.io/gh/makerdao/keeper/branch/master/graph/badge.svg)](https://codecov.io/gh/makerdao/keeper)
[![Code Climate](https://codeclimate.com/github/makerdao/keeper/badges/gpa.svg)](https://codeclimate.com/github/makerdao/keeper)
[![Issue Count](https://codeclimate.com/github/makerdao/keeper/badges/issue_count.svg)](https://codeclimate.com/github/makerdao/keeper)

## Introduction

The _SAI Stablecoin System_, as well as the _DAI Stablecoin System_ in the future,
both rely on external agents, often called _keepers_, to automate certain operations
around the Ethereum blockchain.

This project contains a set of reference keepers, which can either be run directly
by profit-seeking parties, or can be used by them as a foundation for building
their own, more sophisticated keepers.

As a part of the reference keeper implementation, an API around most of the
_SAI Stablecoin System_ contracts has been created. It can be used not only by
keepers, but may also be found useful by authors of some other, unrelated utilities
aiming to interact with these contracts.

## Installation

This project uses *Python 3.6.1*.

In order to install required third-party packages please execute:
```
pip install -r requirements.txt
```

### Known macOS issues

In order for the requirements to install correctly on _macOS_, please install
`openssl` and `libtool` using Homebrew:
```
brew install openssl libtool
```

and set the `LDFLAGS` environment variable before you run `pip install -r requirements.txt`:
```
export LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" 
```

## Reference keepers

This sections lists and briefly describes a set of reference keepers present in this project.

### `keeper-sai-bite`

SAI keeper to bite undercollateralized cups.

This keeper constantly looks for unsafe cups and bites them the moment they become
unsafe. Ultimately, it should take into account the profit it can make by processing
the resulting collateral via `bust` and only waste gas on `bite` if it can make it up
by subsequent arbitrage. For now, it is a dumb keeper that just bites every cup
that can be bitten.

### `keeper-sai-arbitrage`

TODO

### `keeper-sai-top-up`

TODO

### `keeper-sai-maker-otc`

TODO

### `keeper-sai-maker-etherdelta`

TODO

## Running keepers

An individual script in the `bin` directory is present for each keeper. For example, `keeper-sai-bite`
can be run with:
```bash
bin/keeper-sai-bite --eth-from 0x0101010101010101010101010101010101010101
```

As keepers tend to die at times, in any serious environment they should be run by a tool
which can restart them if they fail. It could be _systemd_, but if you don't want to set it up,
a simple `bin/run-forever` script has been provided. Its job is to simply restart the
specified program as long as it's return code is non-zero.

For example you could run the same `keeper-sai-bite` keeper like that:
```bash
bin/run-forever bin/keeper-sai-bite --eth-from 0x0101010101010101010101010101010101010101
```
so it gets automatically restarted every time it fails.

## APIs for smart contracts

The current version provides APIs for `Tub`, `Lpc`, `ERC20Token`, `DSValue` and in addition
also for `SimpleMarket` (OasisDEX/OTC). There is also a working API around `AuctionManager`
and `SplittingAuctionManager`, but they will be used in _DAI Stablecoin System_, not in
_SAI Stablecoin System_.

You can find the full documentation of the APIs here: http://maker-keeper-docs.surge.sh.

**Beware!** This is the first version of the APIs and they will definitely change
and/or evolve in the future.
