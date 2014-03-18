# coding=utf-8
__author__ = "Gareth Coles"

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.events.general import MessageSent
from system.plugin import PluginObject
from system.protocols.generic.user import User
from utils.data import YamlData

from chef import Chef
from dialectizer import Dialectizer
from fudd import Fudd
from lower import Lower
from olde import Olde
from reverse import Reverse
from upper import Upper


class Plugin(PluginObject):

    commands = None
    data = None
    events = None

    dialectizers = {"chef": Chef(),
                    "fudd": Fudd(),
                    "lower": Lower(),
                    "off": Dialectizer(),
                    "olde": Olde(),
                    "reverse": Reverse(),
                    "upper": Upper()}

    def setup(self):
        self.commands = CommandManager.instance()
        self.events = EventManager.instance()

        self.data = YamlData("plugins/dialectizer/settings.yml")

        self.events.add_callback("MessageSent", self, self.handle_msg_sent,
                                 1)
        self.commands.register_command("dialectizer", self.dialectizer_command,
                                       self, "dialectizer.set")
        self.commands.register_command("dialectiser", self.dialectizer_command,
                                       self, "dialectizer.set")

    def handle_msg_sent(self, event=MessageSent):
        if isinstance(event.target, User):
            return

        name = event.caller.name
        target = event.target.name

        with self.data:
            if not name in self.data:
                self.data[name] = {}

            if not target in self.data[name]:
                self.data[name][target] = "off"

        subber = self.dialectizers[self.data[name][target]]

        message = event.message
        message = subber.sub(message)
        event.message = message

    def dialectizer_command(self, protocol, caller, source, command, raw_args,
                            parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        if isinstance(source, User):
            caller.respond("This command only applies to channels.")
            return
        if not len(args) > 0:
            caller.respond("Usage: {CHARS}dialectizer <dialectizer>")
            caller.respond("Available dialectizers: %s"
                           % ", ".join(self.dialectizers.keys()))
            return

        with self.data:
            if not protocol.name in self.data:
                self.data[protocol.name] = {}

            if not source.name in self.data[protocol.name]:
                self.data[protocol.name][source.name] = "off"

            setting = args[0].lower()
            if not setting in self.dialectizers:
                caller.respond("Unknown dialectizer: %s" % setting)
                return

            self.data[protocol.name][source.name] = setting
            caller.respond("Dialectizer set to '%s'" % setting)
