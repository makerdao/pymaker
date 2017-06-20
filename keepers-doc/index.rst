Sample keepers
==============

A few sample keepers have been created to demonstrate how the `maker.py` API can be used:

- a keeper to initiate liquidation (`bite`) of unsafe cups,
- a keeper to automatically top-up cups before they get too close to the liquidation threshold,
- a keeper to use arbitrage opportunities to earn money around `Maker` contracts.

SaiBite.py
----------

A keeper to initiate liquidation (`bite`) of unsafe cups.

From `keepers/SaiBite.py`:

.. literalinclude:: ../keepers/SaiBite.py
    :language: python

SaiTopUpCups.py
---------------

A keeper to automatically top-up cups before they get too close to the liquidation threshold.

From `keepers/SaiTopUpCups.py`:

.. literalinclude:: ../keepers/SaiTopUpCups.py
    :language: python
    :linenos:

SaiArbitrage.py
---------------

A keeper to use arbitrage opportunities to earn money executing transactions between `Tub`, `Lpc` and OasisDEX.

From `keepers/SaiArbitrage.py`:

.. literalinclude:: ../keepers/SaiArbitrage.py
    :language: python
    :linenos:

and also some other files.
