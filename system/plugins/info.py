# coding=utf-8
import weakref

"""
This module contains a class that represents plugin information

This information is loaded when the plugins are scanned, from their relevant
YAML-based .plug files. It also contains a reference to the plugin itself,
if it's loaded, but this is deprecated.
"""

__author__ = 'Gareth Coles'


class Info(object):
    """
    Encapsulation of plugin information
    """

    data = None

    core = None
    info = None

    def __init__(self, yaml_data, plugin_object=None):
        """
        Instantiate the class, initializing it with a dict of data loaded
        from a .plug file and optionally a plugin object

        :param yaml_data: The plugin's data as loaded
        :type yaml_data: dict
        """

        self.data = yaml_data

        if plugin_object:
            self._plugin_object = weakref.ref(plugin_object)

        if "core" in self.data:
            core = self.data["core"]
            self.name = core["name"]
            self.module = core["module"]

            if "type" in core:
                self.type = core["type"]
            else:
                self.type = "python"

            if "dependencies" in core:
                self.dependencies = core["dependencies"]
            else:
                self.dependencies = []

        if "info" in self.data:
            info = self.data["info"]
            self.version = info["version"]
            self.description = info["description"]
            self.author = info["author"]
            self.website = info["website"]
            self.copyright = info["copyright"]
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
