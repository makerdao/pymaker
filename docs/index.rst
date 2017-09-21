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

.. autoclass:: keeper.api.Address
    :members:

Transact
~~~~~~~~

.. autoclass:: keeper.api.Transact
    :members:

Calldata
~~~~~~~~

.. autoclass:: keeper.api.Calldata
    :members:

Invocation
~~~~~~~~~~

.. autoclass:: keeper.api.Invocation
    :members:

Receipt
~~~~~~~

.. autoclass:: keeper.api.Receipt
    :members:

Transfer
~~~~~~~~

.. autoclass:: keeper.api.Transfer
    :members:


Numeric types
-------------

Most of the numeric data throughout the entire platform is kept as either `Wad` (18-digit precision type)
or `Ray` (27-digit precision type).

Wad
~~~

.. autoclass:: keeper.api.numeric.Wad
    :members:

Ray
~~~

.. autoclass:: keeper.api.numeric.Ray
    :members:


Gas price
---------

.. autoclass:: keeper.api.gas.GasPrice
    :members:

The following implementations of `GasPrice` are available:

DefaultGasPrice
~~~~~~~~~~~~~~~

.. autoclass:: keeper.api.gas.DefaultGasPrice
    :members:

FixedGasPrice
~~~~~~~~~~~~~

.. autoclass:: keeper.api.gas.FixedGasPrice
    :members:

IncreasingGasPrice
~~~~~~~~~~~~~~~~~~

.. autoclass:: keeper.api.gas.IncreasingGasPrice
    :members:


Approvals
---------

.. automodule:: keeper.api.approval
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

.. autoclass:: keeper.api.token.ERC20Token
    :members:

DSToken
"""""""

.. autoclass:: keeper.api.token.DSToken
    :members:

DSEthToken
""""""""""

.. autoclass:: keeper.api.token.DSEthToken
    :members:


Exchanges
~~~~~~~~~

Both `OsaisDEX` and `EtherDelta` are independent of `SAI Stablecoin System`, but as a decentralized exchanges
they provide arbitrage opportunities for profit-seeking agents, so an API has been created around them as well.

OasisDEX
""""""""

.. automodule:: keeper.api.oasis
    :members:

EtherDelta
""""""""""

.. automodule:: keeper.api.etherdelta
    :members:


Authentication
~~~~~~~~~~~~~~

DSGuard
"""""""

.. autoclass:: keeper.api.auth.DSGuard
    :members:

DSRoles
"""""""

.. autoclass:: keeper.api.auth.DSRoles
    :members:


DSProxy
~~~~~~~

.. autoclass:: keeper.api.proxy.DSProxy
    :members:

DSValue
~~~~~~~

.. autoclass:: keeper.api.feed.DSValue
    :members:

DSVault
~~~~~~~

.. autoclass:: keeper.api.vault.DSVault
    :members:



Atomic transactions
-------------------

TxManager
~~~~~~~~~

.. autoclass:: keeper.api.transact.TxManager
    :members:
