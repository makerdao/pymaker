Reference keepers
=================

A few reference keepers have been created:

- a keeper to initiate liquidation (`bite`) of unsafe cups,
- a keeper to automatically top-up cups before they get too close to the liquidation threshold,
- a keeper to use arbitrage opportunities to earn money around `Maker` contracts.

sai_bite.py
-----------

A keeper to initiate liquidation (`bite`) of unsafe cups.

From `keepers/sai_bite.py`:

.. literalinclude:: ../keepers/sai_bite.py
    :language: python

sai_top_up.py
-------------

A keeper to automatically top-up cups before they get too close to the liquidation threshold.

From `keepers/sai_top_up.py`:

.. literalinclude:: ../keepers/sai_top_up.py
    :language: python
    :linenos:

sai_abitrage.py
---------------

A keeper to use arbitrage opportunities to earn money executing transactions between `Tub`, `Lpc` and OasisDEX.

From `keepers/sai_arbitrage.py`:

.. literalinclude:: ../keepers/sai_arbitrage.py
    :language: python
    :linenos:

and also some other files.
