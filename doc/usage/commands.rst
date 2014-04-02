.. _commands:

Big ol' list of commands
========================

This page is simply a big ol' list of commands, the plugin they're from and their
permissions nodes. You can use this as a guide when configuring your instance of
Ultros.

----------------

These plugins are bundled with Ultros. Remember, a **.** is the default command prefix, you can change it in
your protocol-specific configuration file. Commands that don't start with a **.** here do not use the command
prefix.

Auth
----

+-------------------+---------------+-------------------------+---------------------------------------------------+
| Commmand          | Params        | Permission              | Description                                       |
+===================+===============+=========================+===================================================+
| .login            | Username |br| | auth.login              | Allows you to login with your registered account. |
|                   | Password      |                         |                                                   |
+-------------------+---------------+-------------------------+---------------------------------------------------+
| .logout           |               | auth.logout             | Allows you to logout when you've logged in.       |
+-------------------+---------------+-------------------------+---------------------------------------------------+
| .passwd           | Old pass |br| | auth.passwd             | Lets you change your account password.            |
|                   | New pass      |                         |                                                   |
+-------------------+---------------+-------------------------+---------------------------------------------------+
| .register         | Username |br| | auth.register           | Lets you register an account with the bot.        |
|                   | Password      |                         |                                                   |
+-------------------+---------------+-------------------------+---------------------------------------------------+

Bridge
------

+-------------------+--------+------------+--------------+
| Commmand          | Params | Permission | Description  |
+===================+========+============+==============+
| **No commands**   | N/A    | N/A        | N/A          |
+-------------------+--------+------------+--------------+

Dialectizer
-----------

+-------------------+--------+-------------------------+---------------------------------------------------+
| Commmand          | Params | Permission              | Description                                       |
+===================+========+=========================+===================================================+
| **.dialectizer**  | Name   | dialectizer.set         | Allows you to set a dialectizer for the      |br| |
| |br| .dialectiser |        |                         | current channel.                                  |
|                   |        |                         |                                                   |
+-------------------+--------+-------------------------+---------------------------------------------------+

Factoids
--------

+-------------------+---------------+----------------------------+---------------------------------------------------+
| Commmand          | Params        | Permission                 | Description                                       |
+===================+===============+============================+===================================================+
| **Standard commands**                                                                                              |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| .addfactoid       | Location |br| | factoids.add.[location]    | Used to create a new factoid or add a line   |br| |
|                   | Key      |br| |                            | to an existing one.                               |
|                   | Data          |                            |                                                   |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| .delfactoid       | Location |br| | factoids.delete.[location] | Used to delete an existing factoid.               |
|                   | Key      |br| |                            |                                                   |
|                   | Data          |                            |                                                   |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| .getfactoid       | Location |br| | factoids.get.[location]    | Used to get the contents of a factoid.            |
|                   | Key      |br| |                            |                                                   |
|                   | Data          |                            |                                                   |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| .setfactoid       | Location |br| | factoids.set.[location]    | Used to create a new factoid or replace an   |br| |
|                   | Key      |br| |                            | existing one.                                     |
|                   | Data          |                            |                                                   |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| **Short commands for getting factoids**                                                                            |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| ??                | Key           | factoids.get.channel       | Retrieve a factoid in the current channel.        |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| ??<               | Key           | factoids.get.channel       | Retrieve a factoid privately.                     |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| ??>               | Key      |br| | factoids.get.channel       | Retrieve a factoid and have it sent to       |br| |
|                   | Username      |                            | another user privately.                           |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| **Short commands for adding to factoids**                                                                          |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| ??+               | Key      |br| | factoids.add.channel       | Create or add to a factoid for the current   |br| |
|                   | Data          |                            | channel.                                          |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| @?+               | Key      |br| | factoids.add.protocol      | Create or add to a factoid for the current   |br| |
|                   | Data          |                            | protocol.                                         |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| !?+               | Key      |br| | factoids.add.global        | Create or add to a factoid in the global scope.   |
|                   | Data          |                            |                                                   |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| **Short commands for deleting factoids**                                                                           |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| ??-               | Key           | factoids.delete.channel    | Delete a factoid from the current channel.        |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| @?-               | Key           | factoids.delete.protocol   | Delete a factoid from the current protocol.       |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| !?-               | Key           | factoids.delete.global     | Delete a factoid from the global scope.           |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| **Short commands for setting factoids**                                                                            |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| ??~               | Key      |br| | factoids.set.channel       | Create or replace a factoid from the current |br| |
|                   | Data          |                            | channel.                                          |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| @?~               | Key      |br| | factoids.set.protocol      | Create or replace a factoid for the current  |br| |
|                   | Data          |                            | protocol.                                         |
+-------------------+---------------+----------------------------+---------------------------------------------------+
| !?~               | Key      |br| | factoids.set.global        | Create or replace a factoid from the global  |br| |
|                   | Data          |                            | scope.                                            |
+-------------------+---------------+----------------------------+---------------------------------------------------+

.. Footnote links, etc

.. _site: http://ultros.io

.. |br| raw:: html

   <br />
