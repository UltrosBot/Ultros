# coding=utf-8

import system.plugins.plugin as plugin  # Import the plugin base class

"""
An example plugin for you to refer to when you're creating your own ones
"""

__author__ = "Gareth Coles"  # Who are you?


class ExamplePlugin(plugin.PluginObject):  # Create the plugin class
    """
    Example plugin object
    """

    def setup(self):
        """
        Called when the plugin is loaded. Performs initial setup.
        """

        # Register the command in our system
        self.commands.register_command(
            "example",  # The name of the command
            self.example_command,  # The command's function
            self,  # This plugin
            # permission="example.example",  # Required permission for command
            aliases=["example2"],  # Aliases for this command
            default=True  # Whether this command should be available to all
        )

    def example_command(self, protocol, caller, source, command, raw_args,
                        args):
        """
        Command handler for the example command
        """

        if args is None:
            # You'll probably always want this, so you always have
            # arguments if quote-parsing fails
            args = raw_args.split()

        # Send to the channel
        source.respond("Hello, world! You ran the %s command!" % command)

        # Send to the user that ran the command
        caller.respond("Raw arguments: %s" % raw_args)
        caller.respond("Parsed arguments: %s" % args)

        # Send directly through the protocol
        protocol.send_msg(source, "Message through the protocol!")
