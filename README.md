# maker.py

## Rationale

The _Dai Stablecoin System_ relies on auctions for collateral liquidation and
incentivisation of MKR holders. However, despite occasional interest,
there has been little public development of off chain auction agents.

The aim of this project is to develop a framework for bidding on the
auctions and market and allow new trading strategies to be easily implemented.
It will also be easy to simulate this aspect of the system and
potentially search for dynamical instabilities in usage.

## Scope

_Maker.py_ covers two areas:
1. Provides a set of Python APIs to enable easy interaction with
   _Dai Stablecoin System_ smart contracts.
2. Provides a basic set of necessary keepers needed to keep liquidity
   of the system.

## Python APIs for Maker contracts

### AuctionManager and SplittingAuctionManager 

TODO

### DSToken

TODO

### DSValue

TODO

### ERC20Token

TODO

### Tub

TODO

## Keepers

The keepers being part of this project are the most basic implementation, necessary
to keep the Dai Stablecoin System liquid in its initial phase. Having said that,
they were designed with extensibility in mind, so keeper designers can build their
own more sophisticated logic on top of them.

### Installation
```
pip install -r requirements.txt
```

In order for the requirements to install correctly on _macOS_, you may need to set
some environment variables:
```
export LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" 
```

Also, installing `openssl` and `libtool` using Homebrew may help as well.

### Buy&Burn

TODO
