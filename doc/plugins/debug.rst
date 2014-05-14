Core » Debug
*************

.. role:: yaml(code)
   :language: yaml

.. role:: python(code)
   :language: python

+----------------------+-------------------+----------------------------------------------------------------------+
| Obtaining            | Full name         | Description                                                          |
+======================+===================+======================================================================+
| Included with Ultros | **Debug**         | Injects a REPL, which is usable via the **debug** command.           |
+----------------------+-------------------+----------------------------------------------------------------------+

The debug plugin provides a very useful and powerful tool for debugging your bot. It injects a REPL into the bot, on
the main thread, which can be accessed via the **debug** command. Please note that this plugin is intended for
use by developers; if you're just running a bot then you should not play with this.

Using
=====

To run some code, use the **debug** or **dbg** command. Because code is run using **eval**, the bot is unable to relay
output generated as a return value of whatever you're doing - it will be printed to the console instead. To get around
this, we've provided an output function - :python:`output(object)`. Pass it anything you want to be output, and it
shall be so.

.. note:: Making the output function actually work properly was difficult. If you're running things in threads or
          otherwise asynchronously, then this plugin cannot guarantee that it will output to the correct location
          if you run another command while the last one is processing.

Code is run in the scope of the :python:`reload()` function, which is a member of :python:`DebugPlugin`. A useful
member for working with the bot is :python:`self.factory_manager`, which manages most of the bot.

.. warning:: Remember to be careful about who you give access to use this plugin. It can grant users *full control*
             over the machine the bot is running on, depending on the user the bot is running as.

             In short: **Don't let anyone else use this plugin, and don't use it in production!**

Commands and permissions
========================

+-------------------+-------------------+-------------------------+---------------------------------------------------+
| Commmand          | Params            | Permission              | Description                                       |
+===================+===================+=========================+===================================================+
| **.debug**   |br| | **Code**     |br| | debug.debug             | Run some code.                                    |
| .dbg              |                   |                         |                                                   |
+-------------------+-------------------+-------------------------+---------------------------------------------------+

.. Footnote links, etc

.. _site: http://ultros.io

.. |br| raw:: html

   <br />
