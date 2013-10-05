# coding=utf-8
import logging
from operator import itemgetter
from utils.log import getLogger
from utils.misc import output_exception

from types import FunctionType

__author__ = "Gareth Coles"

from system.decorators import Singleton, run_async


@Singleton
class EventManager(object):
    """
    The event manager.

    This class is a singleton in charge of managing both events and callbacks.
    Use EventManager.Instance() or the  manager() function below to grab an
    instance.

    You'll probably want to read the Github documentation to learn how, when
    and why you would use this.

    Remember, priority is handled from highest to lowest, in that order.
    Try not to pick a priority that's the same as another plugin - If you do,
    order will fall back to alphabetical plugin name ordering.

    Public methods:
        add_callback(callback, plugin, function, priority, cancelled=False):
            Add a callback. Call this from your plugin to handle events.
            Note: A plugin may not have more than one handler for a callback.
            You should register a function to call your handlers in order
            inside your plugin if you need this.
            A handler handler. Handlerception!
            - callback:  The name of the callback
            - plugin:    Your plugin object's instance (or self)
            - function:  The callback function
            - priority:  An integer representing where in the order of
                         callbacks the function should be called
            - cancelled: Defaults to False; whether to pass cancelled events
                         in or not
        get_callback(callback, plugin):
            Get a handler dict for a specific callback, in a specific plugin.
            Note: `plugin` is the name of a plugin, not a plugin object.
        get_callbacks(callback):
            Get all handlers (in a list) for a specific callback.
        has_callback(callback):
            Check if a callback exists.
        has_plugin_callback(callback, plugin):
            Check if a plugin registered a handler for a certain callback.
            Note: `plugin` is the name of a plugin, not a plugin object.
        remove_callback(callback, plugin):
            Remove a callback from a plugin.
            Note: `plugin` is the name of a plugin, not a plugin object.
        remove_callbacks(callback):
            Remove a certain callback.
        remove_callbacks_for_plugin(plugin):
            Remove all handlers for a certain plugin.
            Note: `plugin` is the name of a plugin, not a plugin object.
        run_callback(callback, event):
            Run all handlers for a certain callback with an event.
    """

    callbacks = {}
    # {"callback_name":
    #   [
    #     {
    #       "name": name,
    #       "priority": priority,
    #       "function": function,
    #       "cancelled": cancelled,
    #       "filter": function() / None
    #     }
    #   ],
    # }

    def __init__(self):
        self.logger = getLogger("Events")

    def _sort(self, lst):
        return sorted(lst, key=itemgetter("priority", "name"), reverse=True)

    def add_callback(self, callback, plugin, function, priority, fltr=None,
                     cancelled=False):
        if not self.has_callback(callback):
            self.callbacks[callback] = []
        if self.ha_plugin_callback(callback, plugin.info.name):
            raise ValueError("Plugin '%s' has already registered a handler for"
                             " the '%s' callback" %
                             (plugin.info.name, callback))

        current = self.callbacks[callback]

        data = {"name": plugin.info.name,
                "function": function,
                "priority": priority,
                "cancelled": cancelled,
                "filter": fltr}

        self.logger.debug("Adding callback: %s" % data)

        current.append(data)

        self.callbacks[callback] = self._sort(current)

    def get_callback(self, callback, plugin):
        if self.has_callback(callback):
            callbacks = self.get_callbacks(callback)
            for cb in callbacks:
                if cb["name"] == plugin:
                    return cb
            return None
        return None

    def get_callbacks(self, callback):
        if self.has_callback(callback):
            return self.callbacks[callback]
        return None

    def has_callback(self, callback):
        return callback in self.callbacks

    def has_plugin_callback(self, callback, plugin):
        if self.has_callback(callback):
            callbacks = self.get_callbacks(callback)
            for cb in callbacks:
                if cb["name"] == plugin:
                    return True
            return False
        return False

    def remove_callback(self, callback, plugin):
        if self.has_plugin_callback(callback, plugin):
            callbacks = self.get_callbacks(callback)
            done = []
            for cb in callbacks:
                if not cb["name"] == plugin:
                    done.append(cb)
            if len(done) > 0:
                self.callbacks[callback] = self._sort(done)
            else:
                del self.callbacks[callback]

    def remove_callbacks(self, callback):
        if self.has_callback(callback):
            del self.callbacks[callback]

    def remove_callbacks_for_plugin(self, plugin):
        current = self.callbacks.items()
        for key, value in current:
            done = []
            for cb in value:
                if not cb["name"] == plugin:
                    done.append(cb)
            if len(done) > 0:
                self.callbacks[key] = self._sort(done)
            else:
                del self.callbacks[key]

    @run_async
    def run_callback_threaded(self, callback, event):
        self.run_callback(callback, event)

    def run_callback(self, callback, event):
        if self.has_callback(callback):
            for cb in self.get_callbacks(callback):
                try:
                    self.logger.debug("Running callback: %s" % cb)
                    if cb["filter"]:
                        if isinstance(cb["filter"], str):
                            continue
                        elif isinstance(cb["filter"], FunctionType):
                            if not cb["filter"](event):
                                continue
                        else:
                            continue
                    if event.cancelled:
                        if cb["cancelled"]:
                            cb["function"](event)
                        else:
                            self.logger.debug("Not running, event is cancelled"
                                              " and handler doesn't accept"
                                              " cancelled events")
                    else:
                        cb["function"](event)
                except Exception as e:
                    self.logger.warn("Error running callback '%s': %s" %
                                     (callback, e))
                    output_exception(self.logger, logging.WARN)


def manager():
    """
    Get yourself an instance of the event manager.
    """
    return EventManager.Instance()
