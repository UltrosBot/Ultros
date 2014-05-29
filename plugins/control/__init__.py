# coding=utf-8
__author__ = "Gareth Coles"

from system.command_manager import CommandManager

import system.plugin as plugin

from system.translations import Translations
_ = Translations().get()
__ = Translations().get_m()


class ControlPlugin(plugin.PluginObject):

    commands = None

    def setup(self):
        self.commands = CommandManager()

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
            caller.respond(__("Usage: {CHARS}join <channel>"))
            return

        if hasattr(protocol, "join_channel"):
            result = protocol.join_channel(args[0])

            if result:
                caller.respond(__("Done!"))
            else:
                caller.respond(__("Unable to join channel. Does this "
                                  "protocol support joining channels?"))
        else:
            caller.respond(__("This protocol doesn't support channels."))

    def leave_command(self, protocol, caller, source, command, raw_args,
                      args):
        if not len(args) > 0:
            caller.respond(__("Usage: {CHARS}leave <channel>"))
            return

        if hasattr(protocol, "leave_channel"):
            result = protocol.leave_channel(args[0])

            if result:
                caller.respond(__("Done!"))
            else:
                caller.respond(__("Unable to leave channel. Does this "
                                  "protocol support leaving channels?"))
        else:
            caller.respond(__("This protocol doesn't support channels."))

    def raw_command(self, protocol, caller, source, command, raw_args,
                    args):
        if not len(args) > 0:
            caller.respond(__("Usage: {CHARS}raw <data>"))
            return

        if hasattr(protocol, "send_raw"):
            protocol.send_raw(raw_args)

            caller.respond(__("Done!"))
        else:
            caller.respond(__("This protocol doesn't support sending raw "
                              "data."))

    def say_command(self, protocol, caller, source, command, raw_args,
                    args):
        if not len(args) > 1:
            caller.respond(__("Usage: {CHARS}say <target> <message>"))
            return

        channel = args[0]
        message = raw_args[len(channel):].strip()

        if hasattr(protocol, "send_msg"):
            protocol.send_msg(channel, message)

            caller.respond(__("Done!"))
        else:
            caller.respond(__("This protocol doesn't support sending "
                              "messages."))

    def action_command(self, protocol, caller, source, command, raw_args,
                       args):
        if not len(args) > 1:
            caller.respond(__("Usage: {CHARS}action <target> <message>"))
            return

        channel = args[0]
        message = raw_args[len(channel):].strip()

        if hasattr(protocol, "send_action"):
            protocol.send_action(channel, message)

            caller.respond(__("Done!"))
        else:
            caller.respond(__("This protocol doesn't support sending "
                              "actions."))

    def func_command(self, protocol, caller, source, command, raw_args,
                     args):
        if not len(args) > 1:
            caller.respond(__("Usage: {CHARS}func <function> <data>"))
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
                return caller.respond(__("No such function: %s") % func)

            r = x(*_args, **_kwargs)
        except Exception as e:
            self.logger.exception(_("Error running 'func' command!"))
            caller.respond(__("Error: %s") % e)
        else:
            caller.respond(__("Done! Call returned: %s") % r)
