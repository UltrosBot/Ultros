"""
This is an example plugin to give you an idea of how to use Clojure in your
plugins, should you wish to.

We don't really expect anyone to use this, but we've included it to show that
it's actually possible. If you like Lisps, take a look at Clojure and also
ClojurePy, which is what we're using here.
"""

__author__ = 'Gareth Coles'

import cljplugin
import types

# Import main so the lib adds its import handler
from clojure import main  # noqa
from clojure.lang import ifn

from system import plugin
from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.plugins.manager import PluginManager
from system.storage.manager import StorageManager


class ClojurePlugin(plugin.PluginObject):
    """
    Example Clojure plugin
    """

    commands = None
    events = None
    storage = None
    plugman = None

    def __init__(self):
        super(ClojurePlugin, self).__init__()

        self.clj_plugin = cljplugin

    def setup(self):
        # Define this so we have instances of everything we need
        self.commands = CommandManager()
        self.events = EventManager()
        self.storage = StorageManager()
        self.plugman = PluginManager()

        # Now run the actual setup function
        self.wrapper(self.clj_plugin.setup)()

    def __getattribute__(self, item):
        # This is so that you can have a clojure file that behaves like the
        # actual plugin.
        try:
            # Check whether we defined our own attribute on this class
            # noinspection PyCallByClass
            return object.__getattribute__(self, item)
        except AttributeError:
            # If not, use the one on the clojure plugin
            x = getattr(self.clj_plugin, item)

            # Python function or Clojure function
            if isinstance(x, types.FunctionType) or isinstance(x, ifn.IFn):
                # See below for why we do this.
                return self.wrapper(x)

            return x

    # This is used for interop because clojure files are modules, not
    # classes, and so need to be wrapped to have access to self.
    #
    # Use this when you create any functions in Clojure files that need to be
    # passed elsewhere - for example, event and command handlers.

    def wrapper(self, func):
        def inner(*args, **kwargs):
            return func(self, *args, **kwargs)
        return inner
