__author__ = 'Gareth Coles'

import weakref


class Info(object):

    data = None

    core = None
    info = None

    def __init__(self, yaml_data, plugin_object=None):
        """

        :param yaml_data:
        :type yaml_data: dict
        :return:
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

        if self.info is not None:
            self.version = self.info.version
            self.description = self.info.description
            self.author = self.info.author
            self.website = self.info.website
            self.copyright = self.info.copyright

        if hasattr(self.core, "dependencies"):
            self.dependencies = self.core.dependencies
        else:
            self.dependencies = []

    @property
    def plugin_object(self):
        if hasattr(self, "_plugin_object"):
            return self._plugin_object()
        return None

    def set_plugin_object(self, obj):
        self._plugin_object = weakref.ref(obj)
