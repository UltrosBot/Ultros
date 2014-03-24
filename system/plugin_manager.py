# flake8: noqa

"""
This file is the biggest fucking mess you'll ever lay eyes on - and you can
thank the developer of Yapsy for messing up their code so horribly that
one has to jump though a ridiculous number of hoops just to change how
plugin info files are loaded.

Also, for using tabs. Fuck, I hate tabs. Hasn't anyone heard of the PEP?
"""

from distutils.version import StrictVersion

__author__ = 'Gareth Coles'

import os
import yaml

from yapsy.PluginInfo import PluginInfo
from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileAnalyzerWithInfoFile, \
    PluginFileLocator

from system.singleton import Singleton
from utils.log import getLogger

logging = getLogger("Plugins")

PLUGIN_NAME_FORBIDEN_STRING = ";;"  # Yapsy dev doesn't know how to spell


class YamlPluginInfo(PluginInfo):

    def __init__(self, plugin_name, plugin_path):
        self.__details = {}
        self.name = plugin_name
        self.path = plugin_path
        self._ensureDetailsDefaultsAreBackwardCompatible()
        # Storage for stuff created during the plugin lifetime
        self.plugin_object = None
        self.categories = []
        self.error = None

    def __setDetails(self, cfDetails):
        """
        Fill in all details by storing a ``ConfigParser`` instance.

        .. warning: The values for ``plugin_name`` and
                    ``plugin_path`` given a init time will superseed
                    any value found in ``cfDetails`` in section
                    'Core' for the options 'Name' and 'Module' (this
                    is mostly for backward compatibility).
        """
        bkp_name = self.name
        bkp_path = self.path
        self.__details = cfDetails
        self.name = bkp_name
        self.path = bkp_path
        self._ensureDetailsDefaultsAreBackwardCompatible()

    def __getDetails(self):
        return self.__details

    def __getName(self):
        return self.details["core"]["name"]

    def __setName(self, name):
        if not "core" in self.details:
            self.details["core"] = {}
        self.details["core"]["name"] = name

    def __getDependencies(self):
        return self.details["core"]["dependencies"]

    def __setDependencies(self, dependencies):
        if not "core" in self.details:
            self.details["core"] = {}
        self.details["core"]["dependencies"] = dependencies

    def __getPath(self):
        return self.details["core"]["module"]

    def __setPath(self,path):
        if not "core" in self.details:
            self.details["core"] = {}
        self.details["core"]["module"] = path

    def __getVersion(self):
        return StrictVersion(self.details["info"]["version"])

    def setVersion(self, vstring):
        """
        Set the version of the plugin.

        Used by subclasses to provide different handling of the
        version number.
        """
        if isinstance(vstring, StrictVersion):
            vstring = str(vstring)
        if not "info" in self.details:
            self.details["info"] = {}
        self.details["info"]["version"] = vstring

    def __getAuthor(self):
        return self.details["info"]["author"]

    def __setAuthor(self, author):
        if not "info" in self.details:
            self.details["info"] = {}
        self.details["info"]["author"] = author

    def __getCopyright(self):
        return self.details["info"]["copyright"]

    def __setCopyright(self, copyrightTxt):
        if not "info" in self.details:
            self.details["info"] = {}
        self.details["info"]["copyright"] = copyrightTxt

    def __getWebsite(self):
        return self.details["info"]["website"]

    def __setWebsite(self, website):
        if not "info" in self.details:
            self.details["info"] = {}
        self.details["info"]["website"] = website

    def __getDescription(self):
        return self.details["info"]["description"]

    def __setDescription(self, description):
        if not "info" in self.details:
            self.details["info"] = {}
        self.details["info"]["description"] = description

    def __getCategory(self):
        """
        DEPRECATED (>1.9): Mimic former behaviour when what is
        noz the first category was considered as the only one the
        plugin belonged to.
        """
        if self.categories:
            return self.categories[0]
        else:
            return "UnknownCategory"

    def __setCategory(self, c):
        """
        DEPRECATED (>1.9): Mimic former behaviour by making so
        that if a category is set as it it was the only category to
        which the plugin belongs, then a __getCategory will return
        this newly set category.
        """
        self.categories = [c] + self.categories

    name = property(fget=__getName, fset=__setName)
    path = property(fget=__getPath, fset=__setPath)
    version = property(fget=__getVersion, fset=setVersion)
    author = property(fget=__getAuthor, fset=__setAuthor)
    copyright = property(fget=__getCopyright, fset=__setCopyright)
    website = property(fget=__getWebsite, fset=__setWebsite)
    description = property(fget=__getDescription ,fset=__setDescription)
    dependencies = property(fget=__getDependencies ,fset=__setDependencies)
    details = property(fget=__getDetails, fset=__setDetails)
    # deprecated (>1.9): plugins are not longer assocaited to a
    # single category !
    category = property(fget=__getCategory,fset=__setCategory)

    def _ensureDetailsDefaultsAreBackwardCompatible(self):
        """
        Internal helper function.
        """
        if "info" in self.details:
            info = self.details["info"]
            if not "author" in info:
                self.author = "Unknown"
            if not "version" in info:
                self.version = "?.?"
            if not "website" in info:
                self.website = "None"
            if not "copyright" in info:
                self.copyright = "Unknown"
            if not "description" in info:
                self.description = ""
        else:
            self.author = "Unknown"
            self.version = "?.?"
            self.website = "None"
            self.copyright = "Unknown"
            self.description = ""

        if "core" in self.details:
            core = self.details["core"]
            if not "dependencies" in core:
                self.dependencies = []
            else:
                self.dependencies = core["dependencies"]


class PluginFileAnalyzerWithYamlInfoFile(PluginFileAnalyzerWithInfoFile):

    def __init__(self, analyzers=None, plugin_info_cls=YamlPluginInfo):
        super(self.__class__, self).__init__(analyzers, plugin_info_cls)

    def getPluginNameAndModuleFromStream(self,
                                         infoFileObject,
                                         candidate_infofile=None):
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
            logging.debug("Plugin info file has no 'core' section (in '%s')"
                          % candidate_infofile)
            return None, None, None
        if not "name" in data["core"] or not "module" in data["core"]:
            logging.debug("Plugin info file has no 'name' or 'module' section "
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

    def _extractCorePluginInfo(self, directory, filename):
        """
        Gather the core information (name, and module to be loaded)
        about a plugin described by it's info file (found at
        'directory/filename').

        Return a dictionary with name and path of the plugin as well
        as the yaml data containing the info.

        .. note:: This is supposed to be used internally by subclasses
                  and decorators.
        """
        # now we can consider the file as a serious candidate
        if not (isinstance(filename, str) or isinstance(filename, unicode)):
            # filename is a file object: use it
            name, moduleName, data = self.getPluginNameAndModuleFromStream(filename)
        else:
            candidate_infofile = os.path.join(directory, filename)
            # parse the information file to get info about the plugin
            name, moduleName, data = self.getPluginNameAndModuleFromStream(open(candidate_infofile),candidate_infofile)
        if (name, moduleName, data) == (None, None, None):
            return None, None
        infos = {"name": name, "path": os.path.join(directory, moduleName)}
        return infos, data

    def _extractBasicPluginInfo(self, directory, filename):
        """
        Gather some basic documentation about the plugin described by
        its info file (found at 'directory/filename').

        Return an instance of ``self.plugin_info_cls`` containing the
        required information.

        See also:

          ``self._gatherCorePluginInfo``
        """
        infos, data = self._extractCorePluginInfo(directory, filename)
        # collect additional (but usually quite useful) information
        if data["info"]:
            info = data["info"]

            infos["author"] = None
            infos["version"] = None
            infos["website"] = None
            infos["copyright"] = None
            infos["description"] = None
            infos["dependencies"] = []

            if "author" in info:
                infos["author"] = info["author"]
            if "version" in info:
                infos["version"] = info["version"]
            if "website" in info:
                 infos["website"] = info["website"]
            if "copyright" in info:
                infos["copyright"] = info["copyright"]
            if "description" in info:
                infos["description"] = info["description"]
            if "dependencies" in info:
                infos["dependencies"] = info["dependencies"]
        return infos, data


class YamlPluginFileLocator(PluginFileLocator):

    def __init__(self, analyzers=None, plugin_info_cls=YamlPluginInfo):
        if analyzers is None:
            analyzers = [PluginFileAnalyzerWithYamlInfoFile("info_ext")]
        super(YamlPluginFileLocator, self).__init__(analyzers, plugin_info_cls)
        self._analyzers = analyzers
        self._default_plugin_info_cls = YamlPluginInfo


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

    __metaclass__ = Singleton

    def __init__(self,
                 categories_filter=None,
                 directories_list=None,
                 plugin_info_ext=None,
                 plugin_locator=None):

        super(self.__class__, self).__init__(categories_filter,
                                             directories_list,
                                             plugin_info_ext,
                                             plugin_locator)

    def _locatorDecide(self, plugin_info_ext, plugin_locator):
            """
            For backward compatibility, we kept the *plugin_info_ext* argument.
            Thus we may use it if provided. Returns the (possibly modified)
            *plugin_locator*.
            """
            specific_info_ext = plugin_info_ext is not None
            specific_locator = plugin_locator is not None
            res = None
            if not specific_info_ext and not specific_locator:
                # use the default behavior
                res = YamlPluginFileLocator()
            elif not specific_info_ext and specific_locator:
                # plugin_info_ext not used
                res = plugin_locator
            elif not specific_locator and specific_info_ext:
                # plugin_locator not used, and plugin_info_ext provided
                # -> compatibility mode
                res = PluginFileLocator()
                res.setAnalyzers([
                    PluginFileAnalyzerWithInfoFile("info_ext",
                                                   plugin_info_ext)])
            elif specific_info_ext and specific_locator:
                # both provided... issue a warning that tells "plugin_info_ext"
                # will be ignored
                msg = ("Two incompatible arguments (%s) provided:",
                       "'plugin_info_ext' and 'plugin_locator'). Ignoring",
                       "'plugin_info_ext'.")
                raise ValueError(" ".join(msg) % self.__class__.__name__)
            return res