# coding=utf-8

"""
This module contains a class that represents plugin information

This information is loaded when the plugins are scanned, from their relevant
YAML-based .plug files. It also contains a reference to the plugin itself,
if it's loaded, but this is deprecated.
"""

__author__ = 'Gareth Coles'

from system.decorators.log import deprecated
import weakref


class Info(object):
    """
    Encapsulation of plugin information
    """

    data = None

    core = None
    info = None

    def __init__(self, yaml_data, plugin_object=None):
        """
        Instanciate the class, initializing it with a dict of data loaded
        from a .plug file and optionally a plugin object

        :param yaml_data: The plugin's data as loaded
        :type yaml_data: dict
        """

        self.data = yaml_data

        if plugin_object:
            self._plugin_object = weakref.ref(plugin_object)

        for key in yaml_data.keys():
            obj = yaml_data[key]

            if isinstance(obj, dict):
                setattr(self, key, Info(obj))
            else:
                setattr(self, key, obj)

        if self.core is not None:
            self.name = self.core.name
            self.module = self.core.module
            if hasattr(self.core, "dependencies"):
                self.dependencies = self.core.dependencies
            else:
                self.core.dependencies = []
                self.dependencies = []

        if self.info is not None:
            self.version = self.info.version
            self.description = self.info.description
            self.author = self.info.author
            self.website = self.info.website
            self.copyright = self.info.copyright
        else:
            self.version = None
            self.description = None
            self.author = None
            self.website = None
            self.copyright = None

    def get_module(self):
        """
        Get the module this plugin is contained in. Useful for imports.
        """

        if hasattr(self, "module"):
            return "plugins.{}".format(self.module)
        return None

    def set_plugin_object(self, obj):
        """
        Set the plugin object if it wasn't specified in `__init__`
        """

        self._plugin_object = weakref.ref(obj)

    def __json__(self):
        """
        Return a representation of your object that can be json-encoded

        For example, a dict, or a JSON string that represents the data in
        the object
        """

        return {
            "data": self.data,
            "name": self.name,
            "module": self.module,
            "dependencies": self.dependencies,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "website": self.website,
            "copyright": self.copyright
        }

