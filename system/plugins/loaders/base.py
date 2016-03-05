# coding=utf-8
from system.logging.logger import getLogger

__author__ = 'Gareth Coles'


class BasePluginLoader(object):
    logger_name = ""
    factory_manager = None
    plugin_manager = None

    def __init__(self):
        self.logger = getLogger(self.logger_name)

    def setup(self):
        from system.factory_manager import FactoryManager
        from system.plugins.manager import PluginManager

        self.factory_manager = FactoryManager()
        self.plugin_manager = PluginManager()

    def load_plugin(self, info):
        raise NotImplementedError()

    def can_load_plugin(self, info):
        raise NotImplementedError()
