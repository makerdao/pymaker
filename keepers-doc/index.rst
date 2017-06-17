Sample keepers
==============

A few sample keepers have been created to demonstrate how the `maker.py` API can be used:

- a keeper to initiate liquidation (`bite`) of unsafe cups,
- a keeper to automatically top-up cups before they get too close to the liquidation threshold,
- a keeper to process bad debt (`woe`) by buying SAI for SKR on OasisDEX at a lower price and then selling it to the `Tub`.

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

SaiProcessWoe.py
----------------

A keeper to process bad debt (`woe`) by buying SAI for SKR on OasisDEX at a lower price and then selling it to the `Tub`.

From `keepers/SaiProcessWoe.py`:

.. literalinclude:: ../keepers/SaiProcessWoe.py
    :language: python
    :linenos:
