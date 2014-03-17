.. Ultros documentation master file, created by
   sphinx-quickstart on Mon Mar 17 17:25:27 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Command manager
===============

The command manager is in charge of making sure commands go to the right
places, checking command permissions and handling the registration
of commands.

API documentation
=================

.. autoclass:: system.command_manager.CommandManager
    :members:

    .. automethod:: set_factory_manager(self, factory_manager)
    .. automethod:: register_command(self, command, handler, owner, permission=None)
    .. automethod:: unregister_commands_for_owner(self, owner)
    .. automethod:: run_command(self, command, caller, source, protocol, args)
    .. automethod:: add_auth_handler(self, handler)
    .. automethod:: set_permissions_handler(self, handler)
