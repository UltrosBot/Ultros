# coding=utf-8
import importlib
import inspect
import sys

from system.enums import PluginState
from system.factory_manager import FactoryManager
from system.logging.logger import getLogger
from system.plugins.loaders.base import BasePluginLoader
from system.plugins.plugin import PluginObject

from twisted.internet.defer import inlineCallbacks, Deferred, returnValue

__author__ = 'Gareth Coles'


class PythonPluginLoader(BasePluginLoader):
    logger_name = "PythonLoader"

    @inlineCallbacks
    def load_plugin(self, info):  # TODO: Logging
        module = info.get_module()
        self.logger.trace("Module: {}".format(module))

        try:
            if module in sys.modules:
                self.logger.trace("Module exists, reloading..")
                reload(sys.modules[module])
                module_obj = sys.modules[module]
            else:
                module_obj = importlib.import_module(module)

            self.logger.trace("Module object: {}".format(module_obj))

            obj = self.find_plugin_class(module_obj)

            if obj is None:
                self.logger.error(
                    "Unable to find plugin class for plugin: {}".format(
                        info.name
                    )
                )
                returnValue((PluginState.LoadError, None))

        except ImportError:
            self.logger.exception("Unable to import plugin: {}".format(
                info.name
            ))
            returnValue((PluginState.LoadError, None))
        except Exception:
            self.logger.exception("Error loading plugin: {}".format(
                info.name
            ))
            returnValue((PluginState.LoadError, None))
        else:
            try:
                info.set_plugin_object(obj)
                obj.add_variables(info, FactoryManager())
                obj.logger = getLogger(info.name)

                d = obj.setup()

                if isinstance(d, Deferred):
                    _ = yield d
            except Exception:
                self.logger.exception("Error setting up plugin: {}".format(
                    info.name
                ))
                returnValue((PluginState.LoadError, None))
            else:
                returnValue((PluginState.Loaded, obj))

    def find_plugin_class(self, module):
        for name_, clazz in inspect.getmembers(module):
            self.logger.trace("Member: {}".format(name_))
            if inspect.isclass(clazz):
                self.logger.trace("It's a class!")
                if clazz.__module__ == module.__name__:
                    self.logger.trace("It's the right module!")
                    try:
                        if self.is_plugin_class(clazz):
                            return clazz()
                    except RuntimeError:
                        self.logger.exception(
                            "Recursion limit hit while trying to import: "
                            "{}".format(
                                clazz.__name__
                            )
                        )
                        return None
        return None

    def is_plugin_class(self, clazz):
        for parent in clazz.__bases__:
            if parent == PluginObject:
                self.logger.trace("It's the right subclass!")
                return True
        for parent in clazz.__bases__:
            if self.is_plugin_class(parent):
                return True
        return False

    def can_load_plugin(self, info):
        return info.type == "python"

