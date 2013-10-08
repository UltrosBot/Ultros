# flake8: noqa
__author__ = 'Gareth Coles'

import os
import yaml
from yapsy.PluginManager import PluginManager

from system.decorators import Singleton
from utils.log import getLogger

logging = getLogger("Plugins")

PLUGIN_NAME_FORBIDEN_STRING = ";;"  # Yapsy dev doesn't know how to spell


@Singleton
class YamlPluginManagerSingleton(PluginManager):
    """
    A subclass of PluginManager that treats plugin info files as YAML-format
    instead of INI-format, which allows us to specify richer data. We use the
    normal PluginInfo class, however, which means that all the data from the
    file is in PluginInfo.details, as a dict, which makes life a /lot/ easier.

    I know, this file isn't strictly PEP8. I'm having to deal with boilerplate
    from the library, and the dev even decided that tabs were a good idea! So,
    for all you people who are sticklers for standards, sorry, but I can't help
    with this much. At least I corrected the docstrings.
    """

    def _getPluginNameAndModuleFromStream(self,
                                          infoFileObject,
                                          candidate_infofile
                                          ="<buffered info>"):
        """
        Extract the name and module of a plugin from the
        content of the info file that describes it and which
        is stored in infoFileObject.

        .. note:: Prefer using ``_gatherCorePluginInfo``
        instead, whenever possible...

        .. warning:: ``infoFileObject`` must be a file-like
        object: either an opened file for instance or a string
        buffer wrapped in a StringIO instance as another
        example.

        .. note:: ``candidate_infofile`` must be provided
        whenever possible to get better error messages.

        Return a 3-tuple with the name of the plugin, its
        module and the yaml data, if the required info could be
        located, else return ``(None, None, None)``.

        .. note:: This is supposed to be used internally by subclasses
            and decorators.
        """
        # parse the information buffer to get info about the plugin
        try:
            data = yaml.load(infoFileObject)
        except Exception, e:
            logging.debug("Could not parse the plugin file '%s' "
                          "(exception raised was '%s')"
                          % (candidate_infofile, e))
            return None, None, None
        # check if the basic info is available
        if not "core" in data:
            logging.debug("Plugin info file has no 'Core' section (in '%s')"
                          % candidate_infofile)
            return None, None, None
        if not "name" in data["core"] or not "module" in data["core"]:
            logging.debug("Plugin info file has no 'Name' or 'Module' section "
                          "(in '%s')"
                          % candidate_infofile)
            return None, None, None
        # check that the given name is valid
        name = data["core"]["name"]
        name = name.strip()
        if PLUGIN_NAME_FORBIDEN_STRING in name:
            logging.debug("Plugin name contains forbidden character: "
                          "%s (in '%s')" % (PLUGIN_NAME_FORBIDEN_STRING,
                                            candidate_infofile))
            return None, None, None
        return name, data["core"]["module"], data

    def _gatherCorePluginInfo(self, directory, filename):
        """
        Gather the core information (name, and module to be loaded)
        about a plugin described by its info file (found at
        'directory/filename').

        Return an instance of ``self.plugin_info_cls`` and the
        yaml data used to gather the core data *in a tuple*, if the
        required info could be located, else return ``(None,None)``.

        .. note:: This is supposed to be used internally by subclasses
            and decorators.

        """
        # now we can consider the file as a serious candidate
        candidate_infofile = os.path.join(directory, filename)
        # parse the information file to get info about the plugin
        name, moduleName, data = \
            self._getPluginNameAndModuleFromStream(open(candidate_infofile),
                                                   candidate_infofile)
        if (name, moduleName, data) == (None, None, None):
                        return None, None
        # start collecting essential info
        plugin_info = self._plugin_info_cls(name,
                                            os.path.join(directory, moduleName)
                                            )
        return plugin_info, data

    def gatherBasicPluginInfo(self, directory,filename):
        """
        Gather some basic documentation about the plugin described by
        its info file (found at 'directory/filename').

        Return an instance of ``self.plugin_info_cls`` containing the
        required information.

        See also:

          ``self._gatherCorePluginInfo``
        """
        plugin_info, data = self._gatherCorePluginInfo(directory, filename)
        if plugin_info is None:
            return None
        # collect additional (but usually quite useful) information
        if data["info"]:
            info = data["info"]

            plugin_info.author = None
            plugin_info.setVersion(None)
            plugin_info.website = None
            plugin_info.copyright = None
            plugin_info.description = None

            if "author" in info:
                plugin_info.author = info["author"]
            if "version" in info:
                plugin_info.setVersion(info["version"])
            if "website" in info:
                plugin_info.website = info["website"]
            if "copyright" in info:
                plugin_info.copyright = info["copyright"]
            if "description" in info:
                plugin_info.description = info["description"]
        return plugin_info