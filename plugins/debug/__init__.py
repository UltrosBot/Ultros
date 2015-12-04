"""
Debug plugin - Used to debug internal parts of thh code from a chat network.

This allows direct access to the interpreter, so it's quite a dangerous
plugin - don't give command access to someone you don't trust to delete
all your files!

This also does a few different monitoring tasks.
"""

import code

from kitchen.text.converters import to_bytes

from plugins.debug.interpreter import Interpreter
from plugins.debug.monitors import UncollectableMonitor

from system.plugins.plugin import PluginObject
from system.translations import Translations

__author__ = 'Gareth Coles'
__all__ = ["DebugPlugin"]

__ = Translations().get_m()

PyCF_DONT_IMPLY_DEDENT = 0x200


class DebugPlugin(PluginObject):
    """
    Debug plugin object
    """

    interpreter = None

    caller = None
    protocol = None
    source = None

    monitors = []

    def setup(self):
        """
        The list of bridging rules
        """

        self.reload()

        self.commands.register_command(
            "debug", self.debug_cmd, self, "debug.debug", aliases=["dbg"]
        )

    def output(self, message):
        """
        Non-threadsafe function for outputting to the current target
        """

        source = self.source
        message = to_bytes(message)
        message = message.replace("\r", "")

        if "\n" not in message:
            out = [message]
        else:
            out = message.split("\n")

        if out[-1].strip() == "":
            out = out[:len(out) - 1]

        for line in out:
            source.respond(__("[DEBUG] %s") % line)

    def reload(self):
        """
        Reload and restart the interpreter and monitors
        """

        self.monitors = []
        self.monitors.append(UncollectableMonitor(self.logger))

        output = self.output

        self.interpreter = Interpreter(locals())
        self.interpreter.set_output(self.output)

        return True

    def debug_cmd(self, protocol, caller, source, command, raw_args,
                  parsed_args):
        """
        Command handler for the debug command
        """

        self.source = source
        self.caller = caller
        self.protocol = protocol

        try:
            c_obj = code.compile_command(raw_args)
        except SyntaxError as e:
            self.output(__("Syntax error: %s") % e.text)
            return
        except (OverflowError, ValueError) as e:
            self.output(__("Invalid literal: %s") % e.msg)
            return
        except Exception as e:
            self.output("%s" % e)
            return

        try:
            self.interpreter.runcode(c_obj)
        except Exception as e:
            self.output("%s" % e)
            return
