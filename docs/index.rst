Maker Keeper API
================

The Maker Keeper API exists to provide a simple way of interacting with a set of smart contracts that create
the `SAI Stablecoin System`. It is meant to evolve towards the `DAI Stablecoin System` in the future.

They were designed to simplify and facilitate creation of external profit-seeking agents, usually called keepers,
that operate around the stablecoin set of smart contracts. The API can also be used to automate certain tasks for
other entities involved in the `Sai Stablecoin System`, like SAI issuers or traders.

**Beware!** These APIs are still in a very early stage of development and they will very likely change
and/or evolve together with the `SAI Stablecoin System`.


General
-------

Address
~~~~~~~

.. autoclass:: pymaker.Address
    :members:

Transact
~~~~~~~~

.. autoclass:: pymaker.Transact
    :members:

Calldata
~~~~~~~~

.. autoclass:: pymaker.Calldata
    :members:

Invocation
~~~~~~~~~~

.. autoclass:: pymaker.Invocation
    :members:

Receipt
~~~~~~~

.. autoclass:: pymaker.Receipt
    :members:

Transfer
~~~~~~~~

.. autoclass:: pymaker.Transfer
    :members:


Numeric types
-------------

Most of the numeric data throughout the entire platform is kept as either `Wad` (18-digit precision type)
or `Ray` (27-digit precision type).

Wad
~~~

.. autoclass:: pymaker.numeric.Wad
    :members:

Ray
~~~

.. autoclass:: pymaker.numeric.Ray
    :members:


Gas price
---------

.. autoclass:: pymaker.gas.GasPrice
    :members:

The following implementations of `GasPrice` are available:

DefaultGasPrice
~~~~~~~~~~~~~~~

.. autoclass:: pymaker.gas.DefaultGasPrice
    :members:

FixedGasPrice
~~~~~~~~~~~~~

.. autoclass:: pymaker.gas.FixedGasPrice
    :members:

IncreasingGasPrice
~~~~~~~~~~~~~~~~~~

.. autoclass:: pymaker.gas.IncreasingGasPrice
    :members:


Approvals
---------

.. automodule:: pymaker.approval
    :members:


Contracts
---------

SAI Stablecoin
~~~~~~~~~~~~~~

The two core smart contracts of the `SAI Stablecoin System` are ``Tub`` and ``Lpc``.

.. toctree::
    api.sai

ERC20
~~~~~

ERC20Token
""""""""""

.. autoclass:: pymaker.token.ERC20Token
    :members:

DSToken
"""""""

.. autoclass:: pymaker.token.DSToken
    :members:

DSEthToken
""""""""""

.. autoclass:: pymaker.token.DSEthToken
    :members:


Exchanges
~~~~~~~~~

Both `OsaisDEX` and `EtherDelta` are independent of `SAI Stablecoin System`, but as a decentralized exchanges
they provide arbitrage opportunities for profit-seeking agents, so an API has been created around them as well.

OasisDEX
""""""""

.. automodule:: pymaker.oasis
    :members:

EtherDelta
""""""""""

.. automodule:: pymaker.etherdelta
    :members:


Authentication
~~~~~~~~~~~~~~

DSGuard
"""""""

.. autoclass:: pymaker.auth.DSGuard
    :members:


DSValue
~~~~~~~

.. autoclass:: pymaker.feed.DSValue
    :members:

DSVault
~~~~~~~

.. autoclass:: pymaker.vault.DSVault
    :members:



Atomic transactions
-------------------

TxManager
~~~~~~~~~

.. autoclass:: pymaker.transact.TxManager
    :members:
