# coding=utf-8
__author__ = "Gareth Coles"

from system.command_manager import CommandManager
from system.plugin import PluginObject
from system.storage.manager import StorageManager


class Plugin(PluginObject):

    commands = None
    data = None
    events = None
    storage = None

    def setup(self):
        self.commands = CommandManager()
        self.storage = StorageManager()

        self.commands.register_command("join", self.join_command,
                                       self, "control.join")
        self.commands.register_command("leave", self.leave_command,
                                       self, "control.leave")
        self.commands.register_command("say", self.say_command,
                                       self, "control.say")
        self.commands.register_command("action", self.action_command,
                                       self, "control.action")
        self.commands.register_command("raw", self.raw_command,
                                       self, "control.raw")
        self.commands.register_command("func", self.func_command,
                                       self, "control.func")

    def join_command(self, protocol, caller, source, command, raw_args,
                     args):
        if not len(args) > 0:
            caller.respond("Usage: {CHARS}join <channel>")
            return

        if hasattr(protocol, "join_channel"):
            result = protocol.join_channel(args[0])

            if result:
                caller.respond("Done!")
            else:
                caller.respond("Unable to join channel. Does this protocol "
                               "support joining channels?")
        else:
            caller.respond("This protocol doesn't support channels.")

    def leave_command(self, protocol, caller, source, command, raw_args,
                      args):
        if not len(args) > 0:
            caller.respond("Usage: {CHARS}leave <channel>")
            return

        if hasattr(protocol, "leave_channel"):
            result = protocol.leave_channel(args[0])

            if result:
                caller.respond("Done!")
            else:
                caller.respond("Unable to leave channel. Does this protocol "
                               "support leaving channels?")
        else:
            caller.respond("This protocol doesn't support channels.")

    def raw_command(self, protocol, caller, source, command, raw_args,
                    args):
        if not len(args) > 0:
            caller.respond("Usage: {CHARS}raw <data>")
            return

        if hasattr(protocol, "send_raw"):
            protocol.send_raw(raw_args)

            caller.respond("Done!")
        else:
            caller.respond("This protocol doesn't support sending raw data.")

    def say_command(self, protocol, caller, source, command, raw_args,
                    args):
        if not len(args) > 1:
            caller.respond("Usage: {CHARS}say <target> <message>")
            return

        channel = args[0]
        message = raw_args[len(channel):].strip()

        if hasattr(protocol, "send_msg"):
            protocol.send_msg(channel, message)

            caller.respond("Done!")
        else:
            caller.respond("This protocol doesn't support sending messages.")

    def action_command(self, protocol, caller, source, command, raw_args,
                       args):
        if not len(args) > 1:
            caller.respond("Usage: {CHARS}action <target> <message>")
            return

        channel = args[0]
        message = raw_args[len(channel):].strip()

        if hasattr(protocol, "send_action"):
            protocol.send_action(channel, message)

            caller.respond("Done!")
        else:
            caller.respond("This protocol doesn't support sending actions.")

    def func_command(self, protocol, caller, source, command, raw_args,
                     args):
        if not len(args) > 1:
            caller.respond("Usage: {CHARS}func <function> <data>")
            return

        func = args[0]
        arguments = args[1:]

        _args = []
        _kwargs = {}

        for arg in arguments:
            if "=" in arg:
                pos = arg.find("=")
                if arg[pos - 1] != "\\":
                    split = arg.split("=", 1)
                    _kwargs[split[0]] = split[1]
            else:
                _args.append(arg)

        try:
            x = getattr(protocol, func, None)

            if not x:
                return caller.respond("No such function: %s" % func)

            r = x(*_args, **_kwargs)
        except Exception as e:
            self.logger.exception("Error running 'func' command!")
            caller.respond("Error: %s" % e)
        else:
            caller.respond("Done! Call returned: %s" % r)
