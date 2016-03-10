# coding=utf-8
from system.logging.logger import getLogger

__author__ = 'Gareth Coles'


class BasePluginLoader(object):
    logger_name = ""
    name = ""

    factory_manager = None
    plugin_manager = None

    def __init__(self, factory_manager, plugin_manager):
        self.logger = getLogger(self.logger_name)

        self.factory_manager = factory_manager
        self.plugin_manager = plugin_manager

    def setup(self):
        pass

    def load_plugin(self, info):
        raise NotImplementedError()

    def can_load_plugin(self, info):
        raise NotImplementedError()
