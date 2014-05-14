# coding=utf-8

"""
A bunch of classes for working with data. These are to be used in your
plugins. There's several different ones to choose from, each will store
data using a different format and sometimes method. There are, so far, two
types of data storage, encapsulating four classes.

* Key-value  (Dictionary-like)
  * YAML-format with dict-like access and thread safety
  * JSON-format with dict-like access and thread safety
  * In-memory dict-like storage with tread-safety. This is for plugins to
    insert where they need to change the data object of something for some
    reason.
* Relational (SQL)
  * SQLite-format with cursors and thread safety. Also supports in-memory
    storage by specifying ":memory:" as the filename.
"""

__author__ = "Gareth Coles"

import json
import os
import pprint
import yaml

from threading import Lock
from twisted.enterprise import adbapi

from system.storage import formats
from utils.log import getLogger


class Data(object):
    """
    Base class for data storage objects, mostly for type-checking.
    """
    #: Whether the file is editable
    editable = False

    #: Could also be "json" or "yaml", for syntax highlighting purposes
    #: Set this to None if the file can't be represented or edited
    representation = None

    #: List of callbacks to be called when the file is reloaded
    callbacks = []

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
        """
        return [False, None]

    def add_callback(self, func):
        """
        Add a callback to be called when the data file is reloaded.

        :param func: The callback to add
        :type func: function
        """
        if func:
            self.callbacks.append(func)
        else:
            raise ValueError("Invalid callback function supplied!")

    def reload(self):
        """
        Reload the data file (re-parse it), if applicable.

        This should also call the registered callbacks.
        """

        for callback in self.callbacks:
            if callback:
                callback()


class YamlData(Data):
    """
    Data object that uses YAML files for storage.

    This is a standard Data object, its base type is a dictionary, so don't
    try to store anything else in this.

    The correct way to use this is with the `with` macro. This ensures both
    thread-safety and that any data edits will be saved when the block has been
    exited.

    If you're not writing any data, then you can just use this object in the
    same way you'd use a dict, but this will not guarantee thread-safety.

    Example:

    with data:
        data["x"]["y"] = "z"
        thing = data["a"]
        # Some other stuff

    This object uses dict-like access methods, including iteration, `keys`
    and `values` methods. Use it how you would a dict. Additionally, the
    following methods are supported..

    Normal dict getters and setters, length, contains, and deletion methods.
    `save()` - Force a flush to file.
    `load()` - Force a reload from file.

    Note: Data access is "jailed" - you can't load a file from outside the data
    directory.

    For sanity's sake, all YAML files should end in .yml - but this is not
    enforced.
    """

    editable = True
    representation = "yaml"

    data = {}

    mutex = Lock()
    context_mutex = Lock()
    _context_guarded = False

    format = formats.YAML

    def __init__(self, filename):
        self.logger = getLogger("Data")
        filename = filename.strip("..")

        folders = filename.split("/")
        folders.pop()
        folders = "/".join(folders)

        if not os.path.exists(folders):
            os.makedirs(folders)

        self.filename = filename
        self.load()

    def load(self):
        """
        Load or reload data from the filesystem.
        """
        if not self._context_guarded:
            with self.mutex:
                self._load()
                super(YamlData, self).reload()
        else:
            self._load()
            super(YamlData, self).reload()

    reload = load

    def _load(self):
        if not os.path.exists(self.filename):
            open(self.filename, "w").close()
        fh = open(self.filename, "r")
        self.data = yaml.load(fh)
        fh.close()
        if not self.data:
            self.data = {}

    def save(self):
        """
        Save data to the filesystem.
        """
        if not self._context_guarded:
            with self.mutex:
                self._save()
        else:
            self._save()

    def _save(self):
        data = yaml.dump(self.data, default_flow_style=False)
        fh = open(self.filename, "w")
        fh.write(data)
        fh.flush()
        fh.close()

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

        with self:  # Python <3
            try:
                fh = open(self.filename, "w")
                fh.write(data)
                fh.flush()
                fh.close()
            except Exception as e:
                success = False
            finally:
                self.reload()
        return success

    def read(self):
        dumped = yaml.dump(self.data, default_flow_style=False)
        return [
            self.editable,
            "# This is the data in memory, and may not actually be what's in "
            "the file.\n\n%s" % dumped
        ]

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

    def __enter__(self):
        with self.context_mutex:
            self._context_guarded = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()
        self._context_guarded = False
        if exc_type is None:
            return True
        return False

    def __getitem__(self, y):
        return self.data.__getitem__(y)

    def __setitem__(self, key, value):
        return self.data.__setitem__(key, value)

    def __delitem__(self, key):
        return self.data.__delitem__(key)

    def __len__(self):
        return self.data.__len__()

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __iter__(self):
        return self.data.__iter__()

    def __str__(self):
        return "<Ultros YAML data handler: %s>" % self.filename

    def __nonzero__(self):
        return True


class MemoryData(Data):
    """
    In-memory dict-like thread-safe storage. This is to be used as a shim where
    you may need to insert a data object directly, without loading data from
    some kind of file. Pass a dictionary instead of a filename to initialize
    this.
    """

    editable = False
    representation = "json"

    data = {}
    format = formats.MEMORY

    mutex = Lock()
    _context_guarded = True

    filename = ":memory:"  # So plugins can check for this easier

    def __init__(self, data_dict):
        self.logger = getLogger("Data")
        self.data = data_dict

    def load(self):
        """
        Does nothing.
        """
        if not self._context_guarded:
            with self.mutex:
                super(MemoryData, self).reload()
                return
        else:
            super(MemoryData, self).reload()
            return

    reload = load

    def save(self):
        """
        Does nothing.
        """
        if not self._context_guarded:
            with self.mutex:
                return
        else:
            return

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

    def __enter__(self):
        with self.mutex:
            self._context_guarded = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context_guarded = False
        if exc_type is None:
            return True
        return False

    def __getitem__(self, y):
        return self.data.__getitem__(y)

    def __setitem__(self, key, value):
        return self.data.__setitem__(key, value)

    def __delitem__(self, key):
        return self.data.__delitem__(key)

    def __len__(self):
        return self.data.__len__()

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __iter__(self):
        return self.data.__iter__()

    def __str__(self):
        return "<Ultros in-memory data handler: %s>" % self.filename

    def __nonzero__(self):
        return True


class JSONData(Data):
    """
    Data object that uses JSON files for storage.

    This is a standard Data object, its base type is a dictionary, so don't
    try to store anything else in this.

    This object is exactly the same as the YAML data handler, but it uses JSON.

    For sanity's sake, all JSON files should end in .json - but this is not
    enforced.
    """

    editable = True
    representation = "json"

    data = {}
    format = formats.JSON

    mutex = Lock()
    context_mutex = Lock()
    _context_guarded = False

    def __init__(self, filename):
        self.logger = getLogger("Data")
        filename = filename.strip("..")

        folders = filename.split("/")
        folders.pop()
        folders = "/".join(folders)

        if not os.path.exists(folders):
            os.makedirs(folders)

        self.filename = filename
        self.load()

    def load(self):
        """
        Load or reload data from the filesystem.
        """
        if not self._context_guarded:
            with self.mutex:
                self._load()
                super(JSONData, self).reload()
        else:
            self._load()
            super(JSONData, self).reload()

    reload = load

    def _load(self):
        if not os.path.exists(self.filename):
            f = open(self.filename, "w")
            f.write("{}")
            f.flush()
            f.close()
        fh = open(self.filename, "r")
        self.data = json.load(fh)
        fh.close()
        if not self.data:
            self.data = {}

    def save(self):
        """
        Save data to the filesystem.
        """
        if not self._context_guarded:
            with self.mutex:
                self._save()
        else:
            self._save()

    def _save(self):
        data = json.dumps(self.data, indent=4, sort_keys=True,
                          separators=(",", ": "))
        fh = open(self.filename, "w")
        fh.write(data)
        fh.flush()
        fh.close()

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

        with self:  # Python <3
            try:
                fh = open(self.filename, "w")
                fh.write(data)
                fh.flush()
                fh.close()
            except Exception as e:
                success = False
            finally:
                self.reload()
        return success

    def read(self):
        dumped = json.dumps(self.data, indent=4, sort_keys=True,
                            separators=(",", ": "))

        return [self.editable, dumped]

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def get(self, key, default):
        return self.data.get(key, default)

    def __enter__(self):
        with self.context_mutex:
            self._context_guarded = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()
        self._context_guarded = False
        if exc_type is None:
            return True
        return False

    def __getitem__(self, y):
        return self.data.__getitem__(y)

    def __setitem__(self, key, value):
        return self.data.__setitem__(key, value)

    def __delitem__(self, key):
        return self.data.__delitem__(key)

    def __len__(self):
        return self.data.__len__()

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __iter__(self):
        return self.data.__iter__()

    def __str__(self):
        return "<Ultros JSON data handler: %s>" % self.filename

    def __nonzero__(self):
        return True


class DBAPIData(Data):
    """
    Data object that uses Twisted's async DBAPI adapters.

    Tere is no dictionary access here. Instead, you can
    call the three usual functions directly on the class instance, and
    they'll be passed through to the underlying DBAPI implementation.

    For example::

        d = data.runQuery("SELECT * FROM data WHERE thing = ?", (thing,))
        d.addCallback(...)

    If you need full access to the underlying ConnectionPool, you can use
    the **with** construct::

        with data as c:
            # Do stuff with c here

    To specify your connection info, you'll have to pass in some extra args
    to describe your connection::

        manager.get_file("module:path", *args, **kwargs)

    The first argument here has two uses.

    * As an identifier for the storage manager, for ownership reasons
    * To specify the module to connect with
        * This module MUST implement the DBAPI!

    So, here's some examples::

        # Connect to local SQLite database
        manager.get_file(
            "sqlite3:data/test.sqlite",
            "data/test.sqlite"
        )

        # Connect to remote PostgreSQL with a username and password
        manager.get_file(
            "psycopg2:my.site/database",
            "host": "my.site",
            "user": "root",
            "password": "password",
            "db": "database"
        )

        // Connect to remote MySQL with a username and no password
        manager.get_file(
            "pymysql:my.site/database",
            "host": "my.site",
            "user": "root",
            "db": "database"
        )

        // Connect to local MySQL with no username or password
        manager.get_file(
            "pymysql:my.site/database",
            "host": "localhost",
            "db": "database"
        )

    If there are problems using this database abstraction then you should run
    the bot in debug mode and report the output to us in a ticket.

    Please note that this isn't an ORM - you'll still have to support
    separate SQL dialects yourself.

    More info: https://twistedmatrix.com/documents/12.0.0/core/howto/rdbms.html
    """

    representation = "json"
    format = formats.DBAPI

    pool = None
    info = ""

    def __init__(self, path, *args, **kwargs):
        self.logger = getLogger("DBAPI")

        path = path.replace("//", "/")
        path = path.split("/", 1)[1]

        self.path = path

        self.logger.debug("Path: %s" % path)
        self.logger.debug("Args: %s" % (args or "[]"))
        self.logger.debug("KWArgs: %s" % (kwargs or "{}"))

        parsed_module = path.split(":", 1)[0]
        self.parsed_module = parsed_module
        self.args = args
        self.kwargs = kwargs

        self.logger.debug("Parsed module: %s" % parsed_module)

        self.reconnect()

    def reconnect(self):
        args = self.args
        kwargs = self.kwargs
        self.pool = adbapi.ConnectionPool(self.parsed_module, *args,
                                          cp_reconnect=True, **kwargs)

    def runInteraction(self, *args, **kwargs):
        return self.pool.runInteraction(*args, **kwargs)

    def runOperation(self, *args, **kwargs):
        return self.pool.runOperation(*args, **kwargs)

    def runQuery(self, *args, **kwargs):
        return self.pool.runQuery(*args, **kwargs)

    def serialize(self, yielder):
        # Only used when we don't have a conventional serialization, this
        # should return some json/yaml that provides a /SAMPLE/ of the data.
        # It shouldn't return a full set of data - database tables can be huge.
        # Remember, use the yielder - and remember to .close() it! Seriously,
        # use a try...finally block or the thread will loop forever. You have
        # been warned.
        yielder.close()
        return None

    def __enter__(self):
        return self.pool

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True
        return False

    def __str__(self):
        return "<Ultros DBAPI data handler: %s>" % self.path

    def __nonzero__(self):
        return True
