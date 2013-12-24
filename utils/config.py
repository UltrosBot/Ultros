# coding=utf-8
__author__ = "Gareth Coles"

import json
import logging
import os
import yaml

from utils.misc import output_exception
from utils.log import getLogger


class YamlConfig(object):
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

    data = {}
    exists = True
    fh = None

    def __init__(self, filename):
        self.logger = getLogger("YamlConfig")
        # Some sanitizing here to make sure people can't escape the config dirs
        filename = filename.strip("..")
        self.filename = "config/" + filename
        self.exists = self.reload()

    def reload(self):
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
            return True

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

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


class JSONConfig(object):
    """
    Configuration object that uses JSON files for storage.

    This class is similar to the YAML config handler, but it uses JSON.

    Why does this exist when we have YAML?
    ..heck if I know.

    For sanity's sake, all JSON files should end in .json, but this isn't
        enforced.
    """

    data = {}
    exists = True
    fh = None

    def __init__(self, filename):
        self.logger = getLogger("YamlConfig")
        # Some sanitizing here to make sure people can't escape the config dirs
        filename = filename.strip("..")
        self.filename = "config/" + filename
        self.exists = self.reload()

    def reload(self):
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
            return True

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

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


class Config(YamlConfig):
    """
    DEPRECATED: This is only here until I can replace the Config objects
        used all over the place!
    """

    def __init__(self, filename):
        super(Config, self).__init__(filename)
        self.logger.warn("This class is deprecated, use YamlConfig instead!")


class MemoryConfig(object):
    """
    Just like the normal YamlConfig, but pass it a dict instead of a filename.
    That dict will be used to supply data, instead of a parsed YAML file.

    Aside from that, this object emulates the normal YamlConfig. This is
        intended to be used where Configs are required in the code but you need
        to supply one programmatically.
    """

    data = {}
    exists = True
    fh = None

    def __init__(self, data_dict):
        self.logger = getLogger("MemoryConfig")
        self.filename = ":memory:"
        self.exists = True
        self.data = data_dict

    def reload(self):
        return True

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
