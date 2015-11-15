# coding=utf-8

"""
Various configuration handlers. These work like the data handlers, except
you can't write to them, and they load files from a different folder.

You should absolutely use this if you're loading a user-supplied configuration
that never needs to be written to programmatically. There is no in-between
right now, so you'll have to split your plugin storage between data and
configuration, and this is for a good reason - separating configuration
and data is very, very important.
"""

__author__ = "Gareth Coles"

import datetime
import json
import pprint
import os
import re
import yaml

from system.storage import formats
from system.logging.logger import getLogger

from system.translations import Translations
_ = Translations().get()


class Config(object):
    """
    Base class for configuration objects, mostly for type-checking.
    """
    #: Whether the file is editable
    #: :type: bool
    editable = None

    #: Could also be "json" or "yaml", for syntax highlighting purposes
    #: Set this to None if the file can't be represented or edited
    representation = None

    #: List of callbacks to be called when the file is reloaded
    #: :type: list
    callbacks = None

    @property
    def mtime(self):
        """
        The last modified time of this data file.

        Returns None if this isn't a file-like and can't know this.

        :rtype: datetime.datetime, None
        """
        return None

    def validate(self, data):
        """
        Override this for admin interfaces, where applicable.

        If there are errors on certain lines, you can return something like::

            [ [12, "Dick too big"], [15, "Not enough lube"] ]

        Otherwise, return [True] for a success, or [False, "reason"] for a
        failure.

        :param data: The data to validate
        :type data: Object
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
        :type data: Object
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
        :type func: callable
        """
        if callable(func):
            self.callbacks.append(func)
        else:
            raise ValueError(_("Invalid callback supplied!"))

    def reload(self, run_callbacks=True):
        """
        Reload the data file (and re-parse it), if applicable.

        This should also call the registered callbacks.
        """

        pass


class YamlConfig(Config):
    """
    Configuration object that uses YAML files for storage.

    Pass the constructor a filename - this will be relative to the config
    folder. The file will be loaded and parsed as a YAML file.

    Data access is supplied similarly to a dict: Config[get], but remember
    that you can't write to it!

    If you need to reload the file, use the `reload` function. You can also
    check if a file exists.

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

    @property
    def mtime(self):
        return datetime.datetime.fromtimestamp(
            os.path.getmtime(self.filename)
        )

    def __init__(self, filename):
        self.callbacks = []

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
            self.logger.exception("")
            return False
        else:
            self.data = yaml.safe_load(self.fh)
            if run_callbacks:
                for callback in self.callbacks:
                    try:
                        callback()
                    except Exception:
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
            mark = None
            problem = str(e)

            if hasattr(e, "problem"):
                problem = e.problem
                problem = problem.replace("could not found", "could not find")

            if hasattr(e, "problem_mark"):
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

    def iteritems(self):
        return self.data.iteritems()

    def iterkeys(self):
        return self.data.iterkeys()

    def itervalues(self):
        return self.data.itervalues()

    def values(self):
        return self.data.values()

    def get(self, key, default=None):
        return self.data.get(key, default)

    keys.__doc__ = data.keys.__doc__
    items.__doc__ = data.items.__doc__
    values.__doc__ = data.values.__doc__
    get.__doc__ = data.get.__doc__

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

    @property
    def mtime(self):
        return datetime.datetime.fromtimestamp(
            os.path.getmtime(self.filename)
        )

    def __init__(self, filename):
        self.callbacks = []

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
            self.logger.exception("")
            return False
        else:
            self.data = json.load(self.fh)
            if run_callbacks:
                for callback in self.callbacks:
                    try:
                        callback()
                    except Exception:
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

    def iteritems(self):
        return self.data.iteritems()

    def iterkeys(self):
        return self.data.iterkeys()

    def itervalues(self):
        return self.data.itervalues()

    def values(self):
        return self.data.values()

    def get(self, key, default=None):
        return self.data.get(key, default)

    keys.__doc__ = data.keys.__doc__
    items.__doc__ = data.items.__doc__
    values.__doc__ = data.values.__doc__
    get.__doc__ = data.get.__doc__

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
        self.callbacks = []

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
                except Exception:
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

    def iteritems(self):
        return self.data.iteritems()

    def iterkeys(self):
        return self.data.iterkeys()

    def itervalues(self):
        return self.data.itervalues()

    def values(self):
        return self.data.values()

    def get(self, key, default=None):
        return self.data.get(key, default)

    keys.__doc__ = data.keys.__doc__
    items.__doc__ = data.items.__doc__
    values.__doc__ = data.values.__doc__
    get.__doc__ = data.get.__doc__

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

    def __nonzero__(self):
        return True


class ConfigDirectory(Config):
    editable = False

    directory = ""
    pattern = re.compile(".*")
    recursive = False

    data = {}
    files = []

    def __init__(self, filename, pattern=".*", recursive=False,
                 extension_map=None):
        if extension_map is None:
            extension_map = {
                ".json": JSONConfig,
                ".js": JSONConfig,
                ".yml": YamlConfig,
            }

        self.directory = filename
        self.pattern = re.compile(pattern)
        self.recursive = recursive

        matches = []

        if recursive:
            for root, dirs, files in os.walk(filename):
                for _file in files:
                    if self.pattern.match(_file):
                        path = os.path.join(root, _file)

                        if os.path.isfile(path):
                            matches.append(os.path.join(root, _file))
        else:
            for _file in os.listdir(filename):
                if self.pattern.match(_file):
                    path = os.path.join(filename, _file)

                    if os.path.isfile(path):
                        matches.append(os.path.join(filename, _file))

        for match in matches:
            match = match.replace("\\", "/")  # Windows..
            _, ext = os.path.splitext(match)

            clazz = extension_map.get(ext.lower())

            if clazz is not None:
                instance = clazz(match)

                self.data[match] = instance

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def iteritems(self):
        return self.data.iteritems()

    def iterkeys(self):
        return self.data.iterkeys()

    def itervalues(self):
        return self.data.itervalues()

    def values(self):
        return self.data.values()

    def get(self, key, default=None):
        return self.data.get(key, default)

    keys.__doc__ = data.keys.__doc__
    items.__doc__ = data.items.__doc__
    values.__doc__ = data.values.__doc__
    get.__doc__ = data.get.__doc__

    def __getitem__(self, y):
        return self.data.__getitem__(y)

    def __len__(self):
        return self.data.__len__()

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __iter__(self):
        return self.data.__iter__()

    def __nonzero__(self):
        return True
