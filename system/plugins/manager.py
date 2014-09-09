import importlib
import sys
from system.plugin import PluginObject

__author__ = 'Gareth Coles'

from system.enums import PluginState
from system.plugins.info import Info
from system.singleton import Singleton
from utils.log import getLogger

import glob
import inspect
import yaml


class PluginManager(object):
    __metaclass__ = Singleton

    factory_manager = None

    log = None
    module = ""
    path = ""

    info_objects = {}
    plugin_objects = {}

    def __init__(self, factory_manager, path="./plugins", module="plugins"):
        self.log = getLogger("Plugins")

        self.factory_manager = factory_manager

        self.module = module
        self.path = path

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

    def load_plugins(self, plugins_, passes=0, max_passes=10, output=True):
        plugins = [plug.lower() for plug in plugins_]

        if passes > max_passes:
            self.log.warn("Possible dependency loop detected!")
            self.log.warn("Attempting to load: %s" % ", ".join(plugins))
            return False

        for name in plugins:
            name = name.lower()

            if name not in self.info_objects:
                if output:
                    self.log.warn("Unknown plugin: %s" % name)
                continue

            self.log.debug("Loading plugin: %s" % name)

            info = self.info_objects[name]

            deps = info.core.dependencies
            todo = []

            for dep in deps:
                dep = dep.lower()

                if dep not in self.plugin_objects:
                    if dep not in plugins:
                        self.log.warn("Unable to load plugin: %s - It "
                                      "depends on '%s' but it's not going to "
                                      "be loaded" % (info.name, dep))
                        continue
                    self.log.debug(
                        "Pass %s/%s | Needs dep: %s"
                        % (passes, max_passes, dep)
                    )

                    todo.append(dep)

            if todo:
                passes += 1
                self.load_plugins(
                    todo, passes=passes, max_passes=max_passes, output=output
                )

            result = self.load_plugin(name)

            if result is PluginState.LoadError:
                pass  # Already output
            elif result is PluginState.NotExists:  # Should never happen
                self.log.warn("No such plugin: %s" % name)
            elif result is PluginState.Loaded:
                if output:
                    self.log.info(
                        "Loaded plugin: %s v%s by %s" % (
                            info.name,
                            info.version,
                            info.author
                        )
                    )
            elif result is PluginState.AlreadyLoaded:
                if output:
                    self.log.warn("Plugin already loaded: %s" % info.name)
            elif result is PluginState.Unloaded:  # Should never happen
                self.log.error("Plugin unloaded: %s" % name)
                self.log.error("This was a load operation - THIS SHOULD NEVER "
                               "HAPPEN")
            elif result is PluginState.DependencyMissing:
                pass  # Already output

    def load_plugin(self, name):
        name = name.lower()

        if name not in self.info_objects:
            return PluginState.NotExists

        if name in self.plugin_objects:
            return PluginState.AlreadyLoaded

        info = self.info_objects[name]

        for dep in info.core.dependencies:
            dep = dep.lower()

            if dep not in self.plugin_objects:
                return PluginState.DependencyMissing

        module = info.get_module()

        try:
            self.log.trace("Module: %s" % module)
            obj = None

            if module in sys.modules:
                self.log.trace("Module exists, reloading..")
                reload(sys.modules[module])
                module_obj = sys.modules[module]
            else:
                module_obj = importlib.import_module(module)

            self.log.trace("Module object: %s" % module_obj)

            for name_, clazz in inspect.getmembers(module_obj):
                self.log.trace("Member: %s" % name_)

                if inspect.isclass(clazz):
                    self.log.trace("It's a class!")

                    if clazz.__module__ == module:
                        self.log.trace("It's the right module!")

                        for parent in clazz.__bases__:
                            if parent == PluginObject:
                                self.log.trace("It's the right subclass!")
                                obj = clazz()

            if obj is None:
                self.log.error(
                    "Unable to find plugin class for plugin: %s" % info.name
                )
                return PluginState.LoadError

            self.plugin_objects[name] = obj
        except ImportError:
            self.log.exception("Unable to import plugin: %s" % info.name)
            self.log.debug("Module: %s" % module)
            return PluginState.LoadError
        except Exception:
            self.log.exception("Error loading plugin: %s" % info.name)
            return PluginState.LoadError
        else:
            try:
                info.set_plugin_object(obj)

                obj.add_variables(info, self.factory_manager)
                obj.logger = getLogger(info.name)
                obj.setup()
            except Exception:
                self.log.exception("Error setting up plugin: %s" % info.name)
                return PluginState.LoadError
            else:
                self.plugin_objects[name] = obj
                return PluginState.Loaded

    def unload_plugins(self, output=True):
        if output:
            self.log.info("Unloading %s plugins.." % len(self.plugin_objects))

        for key in self.plugin_objects.keys():
            result = self.unload_plugin(key)

            if result is PluginState.LoadError:
                pass  # Should never happen
            elif result is PluginState.NotExists:
                self.log.warn("No such plugin: %s" % key)
            elif result is PluginState.Loaded:
                pass  # Should never happen
            elif result is PluginState.AlreadyLoaded:
                pass  # Should never happen
            elif result is PluginState.Unloaded:  # Should never happen
                if output:
                    self.log.info("Plugin unloaded: %s" % key)
            elif result is PluginState.DependencyMissing:
                pass  # Should never happen

    def unload_plugin(self, name):
        name = name.lower()

        if name not in self.plugin_objects:
            return PluginState.NotExists

        obj = self.plugin_objects[name]

        self.factory_manager.commands.unregister_commands_for_owner(obj)
        self.factory_manager.event_manager.remove_callbacks_for_plugin(obj)
        self.factory_manager.storage.release_files(obj)

        try:
            obj.deactivate()
        except Exception:
            self.log.exception("Error deactivating plugin: %s" % obj.info.name)

        del self.plugin_objects[name]
        return PluginState.Unloaded

    def reload_plugins(self, output=True):
        plugins = self.plugin_objects.keys()
        self.scan(output)

        for name in plugins:
            c_name = self.get_plugin_info(name).name
            result = self.reload_plugin(name)

            if result is PluginState.LoadError:
                pass  # Already output
            elif result is PluginState.NotExists:
                self.log.warn("Plugin has disappeared: %s" % c_name)
            elif result is PluginState.Loaded:
                if output:
                    self.log.info("Reloaded plugin: %s" % c_name)
            elif result is PluginState.AlreadyLoaded:
                if output:
                    self.log.warn("Plugin already loaded: %s" % c_name)
            elif result is PluginState.Unloaded:
                pass  # Should never happen
            elif result is PluginState.DependencyMissing:
                pass  # Already output

    def reload_plugin(self, name):
        name = name.lower()

        result = self.unload_plugin(name)

        if result is not PluginState.Unloaded:
            return result

        return self.load_plugin(name)

    def get_plugin(self, name):
        name = name.lower()

        if name in self.plugin_objects:
            return self.plugin_objects[name]
        return None

    def get_plugin_info(self, name):
        name = name.lower()

        if name in self.info_objects:
            return self.info_objects[name]
        return False

    def plugin_loaded(self, name):
        name = name.lower()

        return name in self.plugin_objects
