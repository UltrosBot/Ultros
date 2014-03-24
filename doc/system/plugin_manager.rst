Plugin manager
==============

The plugin manager module contains classes that are rewritten forms of Yapsy's
base classes. They're also part of the reason we're locking you to a specific
version of Yapsy - They keep changing their class implementations.

Our implementation here is to allow plugin info files to be in YAML format, which
is a lot harder than it really should be.

You won't have to use these yourself, they're managed internally.

-----------------------

.. automodule:: system.plugin_manager
    :members:
    :undoc-members:
    :show-inheritance:
