# coding=utf-8
from system.plugins.loaders.base import BasePluginLoader

__author__ = 'Gareth Coles'


class PythonPluginLoader(BasePluginLoader):
    def load_plugin(self, info):
        pass

    def get_plugin(self, name):
        pass

    def can_handle_plugin(self, info):
        return info.type == "python"

    def unload_plugin(self, name):
        pass

    def plugin_is_loaded(self, name):
        pass
