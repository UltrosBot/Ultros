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

from system.translations import Translations
_ = Translations().get()


class Config(object):
    """
    Base class for configuration objects, mostly for type-checking.
    """
    #: Whether the file is editable
    editable = False

    #: Could also be "json" or "yaml", for syntax highlighting purposes
    #: Set this to None if the file can't be represented or edited
    representation = None

    #: List of callbacks to be called when the file is reloaded
    callbacks = list()

    def validate(self, data):
        """
        Override this for admin interfaces, where applicable.

        If there are errors on certain lines, you can return something like::
            [ [12, "Dick too big"], [15, "Not enough lube"] ]

        Otherwise, return [True] for a success, or [False, "reason"] for a
        failure.

        :param data: The data to validate
        :type data: (usually) str
        """
        return [True]

    def write(self, data):
        """
        Override this for admin interfaces, where applicable.

        Return True if successful, False if unsuccessful, or None if not
        applicable.

        As this is a config file, don't do any parsing, just write directly
        to file.

        :param data: The data to try to save
        :type data: (usually) str
        """
        return None

    def read(self):
        """
        Override this for admin interfaces, where applicable.
        You should return a list such as the following::

            [True, "data"] # The first arg is whether the data is editable.

        Set the first arg to False if we can't edit the data, and the second
        arg to None if we can't represent the data. Otherwise, data should
        be returned as a string.

        As this is a config file, this should directly read the file and
        return its data without any parsing.
        """
        return [False, None]

    def add_callback(self, func):
        """
        Add a callback to be called when the config file is reloaded.

        :param func: The callback to add
        :type func: function
        """
        if callable(func):
            self.callbacks.append(func)
        else:
            raise ValueError(_("Invalid callback supplied!"))

    def reload(self, run_callbacks=True):
        """
        Reload the data file (re-parse it), if applicable.

        This should also call the registered callbacks.
        """

        pass


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
    editable = True

    data = {}
    format = formats.YAML

    exists = True
    fh = None

    callbacks = list()

    def __init__(self, filename):
        self.logger = getLogger("YamlConfig")
        # Some sanitizing here to make sure people can't escape the config dirs
        filename = filename.strip("..")
        self.filename = filename
        self.exists = self.reload(False)

    def reload(self, run_callbacks=True):
        """
        Reload configuration data from the filesystem.
        """
        if not os.path.exists(self.filename):
            self.logger.error(_("File not found: %s") % self.filename)
            return False
        try:
            self.fh = open(self.filename, "r")
        except Exception:
            output_exception(self.logger, logging.ERROR)
            return False
        else:
            self.data = yaml.safe_load(self.fh)
            if run_callbacks:
                for callback in self.callbacks:
                    try:
                        callback()
                    except:
                        self.logger.exception(_("Error running callback %s")
                                              % callback)
            return True

    load = reload

    def read(self):
        dumped = open(self.filename, "r").read()
        return [self.editable, dumped]

    def validate(self, data):
        try:
            yaml.load(data)
        except yaml.YAMLError as e:
            problem = e.problem
            problem = problem.replace("could not found", "could not find")

            mark = e.problem_mark
            if mark is not None:
                return [[mark.line, problem]]
            return [False, problem]
        return [True]

    def write(self, data):
        success = True

        try:
            fh = open(self.filename, "w")
            fh.write(data)
            fh.flush()
            fh.close()
        except Exception:
            self.logger.exception(_("Error writing file"))
            success = False
        finally:
            self.reload()
        return success

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
        raise RuntimeError(_("Configuration objects are read-only!"))

    def __delitem__(self, key):
        raise RuntimeError(_("Configuration objects are read-only!"))

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
    editable = True

    data = {}
    format = formats.JSON

    exists = True
    fh = None

    def __init__(self, filename):
        self.logger = getLogger("YamlConfig")
        # Some sanitizing here to make sure people can't escape the config dirs
        filename = filename.strip("..")
        self.filename = filename
        self.exists = self.reload(False)

    def reload(self, run_callbacks=True):
        """
        Reload configuration data from the filesystem.
        """
        if not os.path.exists(self.filename):
            self.logger.error(_("File not found: %s") % self.filename)
            return False
        try:
            self.fh = open(self.filename, "r")
        except Exception:
            output_exception(self.logger, logging.ERROR)
            return False
        else:
            self.data = json.load(self.fh)
            if run_callbacks:
                for callback in self.callbacks:
                    try:
                        callback()
                    except:
                        self.logger.exception(_("Error running callback %s")
                                              % callback)
            return True

    load = reload

    def read(self):
        dumped = open(self.filename, "r").read()
        return [self.editable, dumped]

    def validate(self, data):
        try:
            json.loads(data)
        except Exception as e:
            # eg, "Expecting property name: line 1 column 2 (char 1)"
            # We need to parse this manually.
            msg = e.message

            if ":" in msg:
                split = msg.rsplit(":", 1)

                line = split[1].split()
                if "line" in line:
                    index = line.index("line")
                    line = line[index + 1]

                    return [[line, split[0]]]
                return [False, msg]
            return [False, msg]
        return [True]

    def write(self, data):
        success = True

        try:
            fh = open(self.filename, "w")
            fh.write(data)
            fh.flush()
            fh.close()
        except Exception:
            self.logger.exception(_("Error writing file"))
            success = False
        finally:
            self.reload()
            return success

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
        raise RuntimeError(_("Configuration objects are read-only!"))

    def __delitem__(self, key):
        raise RuntimeError(_("Configuration objects are read-only!"))

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

    def reload(self, run_callbacks=True):
        """
        Does nothing.
        """
        if run_callbacks:
            for callback in self.callbacks:
                try:
                    callback()
                except:
                    self.logger.exception(_("Error running callback %s")
                                          % callback)
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
        raise RuntimeError(_("Configuration objects are read-only!"))

    def __delitem__(self, key):
        raise RuntimeError(_("Configuration objects are read-only!"))

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
