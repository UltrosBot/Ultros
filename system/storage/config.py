# coding=utf-8

"""
Various configuration handlers. These work like the data handlers, except
you can't write to them, and they load files from a different folder.

You should absolutely use this if you're loading a user-supplied configuration
that never needs to be written to programmatically. There is no in-between
right now, so you'll have to split your plugin storage between data and
configuration, and this is for a good reason - separating configuration
and data is very, very important.

We've got three types of configuration here, and they're all key-value
dict-like objects.

* Yaml-format configuration
* JSON-format configuration
* In-memory dict-like configuration, to be inserted where you may need to
  pass a configuration around but don't have a file to load from.
"""

__author__ = "Gareth Coles"

import json
import logging
import pprint
import os
import yaml

from system.storage import formats
from utils.misc import output_exception
from utils.log import getLogger


class Config(object):
    """
    Base class for configuration objects, mostly for type-checking.
    """
    #: Whether the file is editable
    editable = False

    #: Could also be "json" or "yaml", for syntax highlighting purposes
    #: Set this to None if the file can't be represented
    representation = None

    #: List of callbacks to be called when the file is reloaded
    callbacks = []

    def read(self):
        """
        Override this for admin interfaces, where applicable.
        You should return a list such as the following::

            [True, "data"] # The first arg is whether the data is editable.

        Set the first arg to False if we can't edit the data, and the second
        arg to None if we can't represent the data. Otherwise, data should
        be returned as a string.
        """
        return [False, None]

    def add_callback(self, func):
        """
        Add a callback to be called when the data file is reloaded.

        :param func: The callback to add
        :type func: function
        """
        self.callbacks.append(func)

    def reload(self):
        """
        Reload the config file (re-parse it), if applicable.

        This should also call the registered callbacks.
        """

        for callback in self.callbacks:
            callback()


class YamlConfig(Config):
    """
    Configuration object that uses YAML files for storage.
    Configuration cannot be written. It can only be read. This is to keep
        configuration separate from data storage.

    Pass the constructor a filename - this will be relative to the config
        folder. The file will be loaded and parsed as a YAML file.

    Data access is supplied similarly to a dict: Config[get], but remember
        that you can't write to it!

    If you need to reload the file, use the `.reload()` function. You can also
        check if a file `.exists`.

    For the sake of keeping things sane, all YAML files should end in .yml, but
        this isn't enforced.
    """

    representation = "yaml"

    data = {}
    format = formats.YAML

    exists = True
    fh = None

    def __init__(self, filename):
        self.logger = getLogger("YamlConfig")
        # Some sanitizing here to make sure people can't escape the config dirs
        filename = filename.strip("..")
        self.filename = filename
        self.exists = self.reload()

    def reload(self):
        """
        Reload configuration data from the filesystem.
        """
        if not os.path.exists(self.filename):
            self.logger.error("File not found: %s" % self.filename)
            return False
        try:
            self.fh = open(self.filename, "r")
        except Exception:
            output_exception(self.logger, logging.ERROR)
            return False
        else:
            self.data = yaml.safe_load(self.fh)
            super(self, YamlConfig).reload()
            return True

    def read(self):
        dumped = open(self.filename, "r").read()
        return [self.editable, dumped]

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def get(self, key, default):
        return self.data.get(key, default)

    keys.__doc__ = data.keys.__doc__
    items.__doc__ = data.items.__doc__
    values.__doc__ = data.values.__doc__

    def __getitem__(self, y):
        return self.data.__getitem__(y)

    def __setitem__(self, key, value):
        raise RuntimeError("Configuration objects are read-only!")

    def __delitem__(self, key):
        raise RuntimeError("Configuration objects are read-only!")

    def __len__(self):
        return self.data.__len__()

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __iter__(self):
        return self.data.__iter__()

    def __reversed__(self):
        return self.data.__reversed__()

    def __nonzero__(self):
        return True


class JSONConfig(Config):
    """
    Configuration object that uses JSON files for storage.

    This class is similar to the YAML config handler, but it uses JSON.

    Why does this exist when we have YAML?
    ..heck if I know. Don't use this unless it makes more sense than YAML.
        If you're generating configs using some tool, don't be lazy and just
        generate JSON. Generate YAML, like a good monkey.

    For sanity's sake, all JSON files should end in .json, but this isn't
        enforced.
    """

    representation = "json"

    data = {}
    format = formats.JSON

    exists = True
    fh = None

    def __init__(self, filename):
        self.logger = getLogger("YamlConfig")
        # Some sanitizing here to make sure people can't escape the config dirs
        filename = filename.strip("..")
        self.filename = filename
        self.exists = self.reload()

    def reload(self):
        """
        Reload configuration data from the filesystem.
        """
        if not os.path.exists(self.filename):
            self.logger.error("File not found: %s" % self.filename)
            return False
        try:
            self.fh = open(self.filename, "r")
        except Exception:
            output_exception(self.logger, logging.ERROR)
            return False
        else:
            self.data = json.load(self.fh)
            super(self, JSONConfig).reload()
            return True

    def read(self):
        dumped = open(self.filename, "r").read()
        return [self.editable, dumped]

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def get(self, key, default):
        return self.data.get(key, default)

    keys.__doc__ = data.keys.__doc__
    items.__doc__ = data.items.__doc__
    values.__doc__ = data.values.__doc__

    def __getitem__(self, y):
        return self.data.__getitem__(y)

    def __setitem__(self, key, value):
        raise RuntimeError("Configuration objects are read-only!")

    def __delitem__(self, key):
        raise RuntimeError("Configuration objects are read-only!")

    def __len__(self):
        return self.data.__len__()

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __iter__(self):
        return self.data.__iter__()

    def __reversed__(self):
        return self.data.__reversed__()

    def __nonzero__(self):
        return True


class MemoryConfig(Config):
    """
    Just like the normal YamlConfig, but pass it a dict instead of a filename.
    That dict will be used to supply data, instead of a parsed YAML file.

    Aside from that, this object emulates the normal YamlConfig. This is
        intended to be used where Configs are required in the code but you need
        to supply one programmatically.
    """

    representation = "json"

    data = {}
    format = formats.MEMORY

    exists = True
    fh = None

    filename = ":memory:"

    def __init__(self, data_dict):
        self.logger = getLogger("MemoryConfig")
        self.exists = True
        self.data = data_dict

    def reload(self):
        """
        Does nothing.
        """
        super(self, MemoryConfig).reload()
        return True

    def read(self):
        dumped = pprint.pformat(self.data)

        return [self.editable, dumped]

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def get(self, key, default):
        return self.data.get(key, default)

    keys.__doc__ = data.keys.__doc__
    items.__doc__ = data.items.__doc__
    values.__doc__ = data.values.__doc__

    def __getitem__(self, y):
        return self.data.__getitem__(y)

    def __setitem__(self, key, value):
        raise RuntimeError("Configuration objects are read-only!")

    def __delitem__(self, key):
        raise RuntimeError("Configuration objects are read-only!")

    def __len__(self):
        return self.data.__len__()

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __iter__(self):
        return self.data.__iter__()

    def __reversed__(self):
        return self.data.__reversed__()

    def __nonzero__(self):
        return True
