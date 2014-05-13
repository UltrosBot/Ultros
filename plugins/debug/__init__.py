__author__ = 'Gareth Coles'

import code

import system.plugin as plugin
from system.command_manager import CommandManager

from .interpreter import Interpreter
from .monitors import UncollectableMonitor

PyCF_DONT_IMPLY_DEDENT = 0x200


class DebugPlugin(plugin.PluginObject):

    commands = None

    interpreter = None

    caller = None
    protocol = None
    source = None

    monitors = []

    def setup(self):
        self.commands = CommandManager()
        self.reload()

        self.monitors.append(UncollectableMonitor(self.logger))

        self.commands.register_command("debug", self.debug_cmd,
                                       self, "debug.debug", aliases=["dbg"])

    def output(self, message):
        source = self.source
        message = str(message)
        message = message.replace("\r", "")

        if "\n" not in message:
            out = [message]
        else:
            out = message.split("\n")

        if out[-1].strip() == "":
            out = out[:len(out) - 1]

        for line in out:
            source.respond("[DEBUG] %s" % line)

    def reload(self):
        output = self.output

        self.interpreter = Interpreter(locals())
        self.interpreter.set_output(self.output)
        return True

    def debug_cmd(self, protocol, caller, source, command, raw_args,
                  parsed_args):
        self.source = source
        self.caller = caller
        self.protocol = protocol

        try:
            c_obj = code.compile_command(raw_args)
        except SyntaxError as e:
            self.output("Syntax error: %s" % e.text)
            return
        except (OverflowError, ValueError) as e:
            self.output("Invalid literal: %s" % e.msg)
            return
        except Exception as e:
            self.output("%s" % e)
            return

        try:
            self.interpreter.runcode(c_obj)
        except Exception as e:
            self.output("%s" % e)
            return
