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

.. automodule:: keeper.api
    :members: Address

Transact
~~~~~~~~

.. automodule:: keeper.api
    :members: Transact

Calldata
~~~~~~~~

.. automodule:: keeper.api
    :members: Calldata

Invocation
~~~~~~~~~~

.. automodule:: keeper.api
    :members: Invocation

Receipt
~~~~~~~

.. automodule:: keeper.api
    :members: Receipt

Transfer
~~~~~~~~

.. automodule:: keeper.api
    :members: Transfer

.. automodule:: keeper.api.approval
    :members:


Numeric types
-------------

Most of the numeric data throughout the entire platform is kept as either `Wad` (18-digit precision type)
or `Ray` (27-digit precision type).

Wad
~~~

.. automodule:: keeper.api.numeric
    :members: Wad

Ray
~~~

.. automodule:: keeper.api.numeric
    :members: Ray


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

.. automodule:: keeper.api.token
    :members: ERC20Token

DSToken
"""""""

.. automodule:: keeper.api.token
    :members: DSToken

DSEthToken
""""""""""

.. automodule:: keeper.api.token
    :members: DSEthToken


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

.. automodule:: keeper.api.auth
    :members: DSGuard

DSRoles
"""""""

.. automodule:: keeper.api.auth
    :members: DSRoles


DSProxy
~~~~~~~

.. automodule:: keeper.api.proxy
    :members: DSProxy

DSValue
~~~~~~~

.. automodule:: keeper.api.feed
    :members: DSValue

DSVault
~~~~~~~

.. automodule:: keeper.api.vault
    :members: DSVault



Atomic transactions
-------------------

TxManager
~~~~~~~~~

.. automodule:: keeper.api.transact
    :members:
