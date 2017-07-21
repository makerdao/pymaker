API Documentation
=================

The `maker.py` API exists to provide a simple way of interacting with a set of smart contracts that create
the `SAI Stablecoin System`. It is meant to evolve towards the `DAI Stablecoin System` in the future.

The API been designed to simplify and facilitate creation of external profit-seeking agents, usually called keepers,
that operate around the stablecoin set of smart contracts. The API can also be used to automate certain tasks for
other entities involved in the `Sai Stablecoin System`, like SAI issuers or traders.

You can find some basic keepers and also some other examples bundled in this project.

Smart contracts
---------------

SAI Stablecoin
~~~~~~~~~~~~~~

The two core smart contracts of the `SAI Stablecoin System` are ``Tub`` and ``Lpc``.

.. toctree::
    api.sai

ERC20
~~~~~

`SAI Stablecoin System` utilizes regular ERC20 tokens. An API has been provided for easy interaction with them.

.. toctree::
    api.token

Data feeds
~~~~~~~~~~

`SAI Stablecoin System` revolves around ``DSValue`` and its descendants, ``DSCache`` and ``Medianizer``.

.. toctree::
    api.feed

OasisDEX
~~~~~~~~

`OsaisDEX` is independent of `SAI Stablecoin System`, but as a decentralized exchange provides arbitraging
opportunities for profit-seeking agents, so an API has been created around it as well.

.. toctree::
    api.oasis

EtherDelta
~~~~~~~~~~

`EtherDelta` is independent of `SAI Stablecoin System`, but as a decentralized exchange provides arbitraging
opportunities for profit-seeking agents, so an API has been created around it as well.

.. toctree::
    api.etherdelta

Numeric types
-------------

Most of the numeric data throughout the entire platform is kept as either `Wad` (18-digit precision type) or `Ray`
(27-digit precision type).

.. automodule:: api.numeric
    :members:


Other classes
-------------

.. automodule:: api
    :members:

.. automodule:: api.approval
    :members:

.. automodule:: api.transact
    :members:
