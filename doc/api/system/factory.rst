Factory
=======

The factory exists purely to create instances of protocols. Each protocol will
get their own factory. Factories are also in charge of dispatching configuration
to their protocols and handling any reconnection attempts.

You will never need to subclass this. Let the factory manager handle it.

-----------------------

.. module:: system.factory

.. autoclass:: Factory
    :members:
    :undoc-members:
    :show-inheritance:
