# coding=utf-8

import glob
import yaml

from copy import copy
from distutils.version import StrictVersion

from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

from system.enums import PluginState
from system.events.manager import EventManager
from system.events.general import PluginUnloadedEvent, PluginLoadedEvent
from system.logging.logger import getLogger
from system.plugins.info import Info
from system.plugins.loaders.python import PythonPluginLoader
from system.singleton import Singleton

__author__ = 'Gareth Coles'

"""
The plugin manager. It manages plugins.

The manager is in charge of discovering, loading, unloading, reloading and
generally looking after all things plugin.
"""

OPERATORS = {
    ">": lambda x, y: x > y,
    ">=": lambda x, y: x >= y,
    "<": lambda x, y: x < y,
    "<=": lambda x, y: x <= y,
    "==": lambda x, y: x == y,
    "!=": lambda x, y: x != y,
}


def MISSING_OPERATOR(x, y):
    return True


class PluginManager(object):
    """
    The plugin manager itself. This is a Singleton.
    """

    __metaclass__ = Singleton

    factory_manager = None

    log = None
    module = ""
    path = ""

    info_objects = {}
    plugin_objects = {}

    events = EventManager()

    def __init__(self, factory_manager=None,
                 path="./plugins", module="plugins"):
        if factory_manager is None:
            raise ValueError("Factory manager cannot be None!")

        self.log = getLogger("Plugins")
        self.loaders = {}

        python_loader = PythonPluginLoader(factory_manager, self)
        self.loaders["python"] = python_loader

        self.factory_manager = factory_manager

        self.module = module
        self.path = path

        try:
            import hy  # noqa
        except ImportError:
            hy = None  # noqa

            self.log.warn("Unable to find Hy - Hy plugins will not load")
            self.log.warn("Install Hy with pip if you need this support")

    def find_loader(self, info):
        for loader in self.loaders.itervalues():
            if loader.can_load_plugin(info):
                return loader
        return None

    def add_loader(self, loader):
        """
        Add a plugin loader, for loading specific types of plugin

        This will fail with a result of False if there's already a loader
        with the same name.

        :param loader: Instance of your plugin loader
        :type loader: BasePluginLoader

        :returns: Whether the loader was added
        :rtype: bool
        """

        if loader.name in self.loaders:
            return False

        self.loaders[loader.name] = loader
        return True

    @inlineCallbacks
    def remove_loader(self, name):
        """
        Remove a plugin loader by name

        This will fail with a result of False if there isn't a loader
        registered with the specified name.

        :param name: Name of the loader to remove
        :type name: str

        :returns: A Deferred, resulting in whether the loader was removed
        :rtype: Deferred(bool)
        """

        if name not in self.loaders:
            returnValue(False)

        to_unload = []
        loader = self.loaders[name]

        for plugin in self.plugin_objects.itervalues():
            if plugin._loader == loader.name:
                to_unload.append(plugin.info.name)

        del loader

        for plugin in to_unload:
            _ = yield self.unload_plugin(plugin)

        del self.loaders[name]
        returnValue(True)

    def scan(self, output=True):
        """
        Scan for all the .plug files available.

        :param output: Whether to output info messages
        """

        self.info_objects = {}
        files = glob.glob("%s/*.plug" % self.path)

        if not files:
            if output:
                self.log.info("No plugins found.")
            return

        self.log.debug("Loading info files..")

        for fn in files:
            try:
                obj = yaml.load(open(fn, "r"))
                c_name = obj["core"]["name"]  # "Cased" name
                name = c_name.lower()

                if name in self.info_objects:
                    self.log.error(
                        "Duplicate plugin name detected: %s" % c_name
                    )
                    self.log.error("Only the first one will be able to load!")
                    continue

                self.info_objects[name] = Info(obj)

                if output:
                    self.log.debug("Found plugin info: %s" % c_name)
            except Exception:
                self.log.exception("Error loading info file: %s" % fn)

        if output:
            self.log.info("%s plugins found." % len(self.info_objects))

        extra = 0

        for k, v in self.plugin_objects.iteritems():
            if k in self.info_objects:
                continue

            extra += 1
            self.info_objects[k] = v.info

        if output:
            if extra > 1:
                self.log.warning("%s plugins have disappeared." % extra)

    @inlineCallbacks
    def load_plugins(self, plugins, output=True):
        """
        Attempt to load up all plugins specified in a list

        This is intended to do the primary plugin load operation on startup,
        using the plugin names specified in the configuration.

        Plugin names are not case-sensitive.

        :param plugins: List of plugin names to look for
        :param output: Whether to output errors and other messages to the log

        :type plugins: list
        :type output: bool

        :returns: A Deferred, resulting in no value
        :rtype: Deferred
        """

        self.loaders["python"].setup()

        # Plugins still needing loaded
        to_load = []
        # Final, ordered, list of plugins to load
        load_order = []

        # Get plugin info objects, etc.
        for name in plugins:
            name = name.lower()

            if name not in self.info_objects:
                if output:
                    self.log.warning("Unknown plugin: %s" % name)
                continue

            info = self.info_objects[name]
            # Store the list of deps separately so we can keep track of the
            # unmet ones, for logging later on
            to_load.append((info, [i.lower() for i in info.dependencies]))

        # Determine order
        has_loaded = True
        while len(to_load) > 0 and has_loaded:
            has_loaded = False
            # Iterate backwards so we can remove items
            for x in xrange(len(to_load) - 1, -1, -1):
                info = to_load[x][0]
                deps = to_load[x][1]

                self.log.trace(
                    "Checking dependencies for plugins: %s" % info.name
                )

                for i, dep in enumerate(copy(deps)):
                    if " " in dep:
                        dep_name, dep_operator, dep_version = dep.split(" ")
                    else:
                        dep_name = dep
                        dep_operator = None
                        dep_version = None

                    operator_func = OPERATORS.get(
                        dep_operator, MISSING_OPERATOR
                    )

                    if dep_version:
                        parsed_dep_version = StrictVersion(dep_version)
                    else:
                        parsed_dep_version = dep_version

                    for loaded in load_order:
                        # I know this isn't super efficient, but it doesn't
                        # matter, it's a tiny list. This comment exists
                        # purely for myself.

                        if loaded.name.lower() == dep_name:
                            self.log.trace("Found a dependency")
                            loaded_version = StrictVersion(loaded.version)

                            if not operator_func(
                                    loaded_version, parsed_dep_version
                            ):
                                break

                            deps[i] = None

                            if deps.count(None) == len(deps):
                                self.log.trace("No more deps")
                                break
                            self.log.trace(deps)

                while None in deps:
                    deps.remove(None)

                if len(deps) == 0:
                    # No outstanding dependencies - safe to load
                    self.log.trace(
                        "All dependencies met, adding to load queue."
                    )
                    load_order.append(info)
                    del to_load[x]
                    has_loaded = True

        # Deal with unloadable plugins
        if len(to_load) > 0:
            for plugin in to_load:
                self.log.warning(
                    'Unable to load plugin "%s" due to failed dependencies: '
                    '%s' %
                    (
                        plugin[0].name,
                        ", ".join(plugin[1])
                    )
                )

        did_load = []

        # Deal with loadable plugins
        for info in load_order:
            self.log.debug("Loading plugin: %s" % info.name)

            result = yield self.load_plugin(info.name)

            if result is PluginState.LoadError:
                self.log.debug("LoadError")
                pass  # Already output by load_plugin
            elif result is PluginState.NotExists:  # Should never happen
                self.log.warning("No such plugin: %s" % info.name)
            elif result is PluginState.Loaded:
                if output:
                    self.log.info(
                        "Loaded plugin: %s v%s by %s" % (
                            info.name,
                            info.version,
                            info.author
                        )
                    )
                did_load.append(info.name)
            elif result is PluginState.AlreadyLoaded:
                if output:
                    self.log.warning("Plugin already loaded: %s" % info.name)
            elif result is PluginState.Unloaded:  # Can actually happen now
                self.log.warn("Plugin unloaded: %s" % info.name)
                self.log.warn("This means the plugin disabled itself - did "
                              "it output anything on its own?")
            elif result is PluginState.DependencyMissing:
                self.log.debug("DependencyMissing")

        self.log.info("Loaded {} plugins: {}".format(
            len(did_load), ", ".join(sorted(did_load))
        ))

    @inlineCallbacks
    def load_plugin(self, name):
        """
        Load a single plugin by its case-insensitive name

        :param name: The name of the plugin to load
        :type name: str

        :return: A Deferred, resulting in a PluginState enum value representing
                 the result
        :rtype: Deferred(PluginState)
        """

        name = name.lower()

        if name not in self.info_objects:
            returnValue(PluginState.NotExists)

        if name in self.plugin_objects:
            returnValue(PluginState.AlreadyLoaded)

        info = self.info_objects[name]

        for dep in info.dependencies:
            dep = dep.lower()

            if " " in dep:
                dep_name, dep_operator, dep_version = dep.split(" ")
            else:
                dep_name = dep
                dep_operator = None
                dep_version = None

            operator_func = OPERATORS.get(
                dep_operator, MISSING_OPERATOR
            )

            if dep_version:
                parsed_dep_version = StrictVersion(dep_version)
            else:
                parsed_dep_version = dep_version

            if dep_name not in self.plugin_objects:
                returnValue(PluginState.DependencyMissing)

            loaded = self.plugin_objects[dep_name]
            loaded_version = StrictVersion(loaded.info.version)

            if not operator_func(loaded_version, parsed_dep_version):
                returnValue(PluginState.DependencyMissing)

        loader = self.find_loader(info)

        result, obj = yield loader.load_plugin(info)

        if result is PluginState.Loaded:
            self.plugin_objects[name] = obj

        event = PluginLoadedEvent(self, obj)
        self.events.run_callback("PluginLoaded", event)

        returnValue(result)

    @inlineCallbacks
    def unload_plugins(self, output=True):
        """
        Unload all loaded plugins

        :param output: A Deferred, resulting in whether to output errors and
                       other messages to the log
        :type output: Deferred(bool)
        """

        if output:
            self.log.info(
                "Unloading {} plugins..".format(len(self.plugin_objects))
            )

        for key in self.plugin_objects.keys():
            result = yield self.unload_plugin(key)

            if result is PluginState.LoadError:
                pass  # Should never happen
            elif result is PluginState.NotExists:
                self.log.warning("No such plugin: {}".format(key))
            elif result is PluginState.Loaded:
                pass  # Should never happen
            elif result is PluginState.AlreadyLoaded:
                pass  # Should never happen
            elif result is PluginState.Unloaded:
                pass  # Output by the unload_plugin function already
            elif result is PluginState.DependencyMissing:
                pass  # Should never happen

    @inlineCallbacks
    def unload_plugin(self, name):
        """
        Unload a single loaded plugin by its case-insensitive name

        :param name: The name of the plugin to unload
        :type name: str

        :return: A Deferred, resulting in a PluginState enum value representing
                 the result
        :rtype: Deferred(PluginState)
        """

        name = name.lower()

        if name not in self.plugin_objects:
            returnValue(PluginState.NotExists)

        obj = self.plugin_objects[name]

        self.factory_manager.commands.unregister_commands_for_owner(obj)
        self.factory_manager.event_manager.remove_callbacks_for_plugin(obj)
        self.factory_manager.storage.release_files(obj)

        try:
            d = obj.deactivate()

            if isinstance(d, Deferred):
                _ = yield d
        except Exception:
            self.log.exception("Error deactivating plugin: %s" % obj.info.name)

        event = PluginUnloadedEvent(self, obj)
        self.events.run_callback("PluginUnloaded", event)

        del self.plugin_objects[name]

        self.log.info("Unloaded plugin: {}".format(name))
        returnValue(PluginState.Unloaded)

    def reload_plugins(self, output=True):
        """
        Reload all loaded plugins

        :param output: Whether to output errors and other messages to the log
        :type output: bool
        """

        plugins = self.plugin_objects.keys()
        self.scan(output)

        for name in plugins:
            c_name = self.get_plugin_info(name).name
            result = self.reload_plugin(name)

            if result is PluginState.LoadError:
                pass  # Already output
            elif result is PluginState.NotExists:
                self.log.warning("Plugin has disappeared: %s" % c_name)
            elif result is PluginState.Loaded:
                if output:
                    self.log.info("Reloaded plugin: %s" % c_name)
            elif result is PluginState.AlreadyLoaded:
                if output:
                    self.log.warning("Plugin already loaded: %s" % c_name)
            elif result is PluginState.Unloaded:
                pass  # Should never happen
            elif result is PluginState.DependencyMissing:
                pass  # Already output

    @inlineCallbacks
    def reload_plugin(self, name):
        """
        Reload a single loaded plugin by its case-insensitive name

        :param name: The name of the plugin to reload
        :type name: str

        :return: A Deferred, resulting in a PluginState enum value representing
                 the result
        :rtype: Deferred(PluginState)
        """

        name = name.lower()

        result = yield self.unload_plugin(name)

        if result is not PluginState.Unloaded:
            returnValue(result)
            r = yield self.load_plugin(name)

            returnValue(r)

    def get_plugin(self, name):
        """
        Get a plugin instance by its case-insensitive name

        returns None if the plugin isn't loaded or doesn't exist

        :param name: The name of the plugin to get
        :type name: str

        :return: PluginObject instance, or None
        """

        name = name.lower()

        if name in self.plugin_objects:
            return self.plugin_objects[name]
        return None

    def get_plugin_info(self, name):
        """
        Get a plugin's info object by its case-insensitive name

        returns None if the plugin doesn't exist

        :param name: The name of the plugin to get the info for
        :type name: str

        :return: Info instance, or None
        """

        name = name.lower()

        if name in self.info_objects:
            return self.info_objects[name]
        return None

    def plugin_loaded(self, name):
        """
        Check whether a plugin is loaded by its case-insensitive name

        :param name: The name of the plugin to check
        :type name: str

        :return: Whether the plugin is loaded
        :rtype: bool
        """

        name = name.lower()

        return name in self.plugin_objects
