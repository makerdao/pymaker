pymaker API
===========

The `pymaker` API exists to provide a simple way of interacting with Maker smart contracts.

It was designed to simplify and facilitate creation of external profit-seeking agents, usually called keepers,
that operate around the stablecoin set of smart contracts. The API can also be used to automate certain tasks for
other entities involved in the platform, like DAI issuers or traders.


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

DAI Stablecoin
~~~~~~~~~~~~~~

Tub
"""

.. autoclass:: pymaker.sai.Tub
    :members:

Tap
"""

.. autoclass:: pymaker.sai.Tap
    :members:

Top
"""

.. autoclass:: pymaker.sai.Top
    :members:

Vox
"""

.. autoclass:: pymaker.sai.Vox
    :members:

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

`OaaisDEX`, `EtherDelta` and `0x` are decentralized exchanges which also provide some arbitrage opportunities
for profit-seeking agents. Because of that an API has been created around them as well. Also an API for
the `Bibox` centralized exchange is present.

OasisDEX
""""""""

.. automodule:: pymaker.oasis
    :members:

EtherDelta
""""""""""

.. automodule:: pymaker.etherdelta
    :members:

0x
""

.. automodule:: pymaker.zrx
    :members:

Bibox
"""""

.. automodule:: pymaker.bibox
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

.. autoclass:: pymaker.transactional.TxManager
    :members:
