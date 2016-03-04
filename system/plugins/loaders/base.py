# coding=utf-8

__author__ = 'Gareth Coles'


class BasePluginLoader(object):
    def load_plugin(self, info):
        raise NotImplementedError()

    def unload_plugin(self, name):
        raise NotImplementedError()

    def can_handle_plugin(self, info):
        raise NotImplementedError()

    def get_plugin(self, name):
        raise NotImplementedError()

    def plugin_is_loaded(self, name):
        raise NotImplementedError()
