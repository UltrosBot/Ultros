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
import sqlite3
import yaml

from threading import Lock

from utils.log import getLogger


class Data(object):
    """
    Base class for data storage objects, mostly for type-checking.
    """
    pass


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

    data = {}

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
        else:
            self._load()

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
        data = yaml.dump(self.data)
        fh = open(self.filename, "w")
        fh.write(data)
        fh.flush()
        fh.close()

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

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

    data = {}

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
                return
        else:
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

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

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

    data = {}

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
        else:
            self._load()

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
        data = json.dumps(self.data)
        fh = open(self.filename, "w")
        fh.write(data)
        fh.flush()
        fh.close()

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


class SqliteData(Data):
    """
    Data object that uses SQLite for storage.

    This is a very different data storage object! There is no dictionary
    access here, instead use the `with...as` construct. This will return
    a standard cursor for you to work with, which will be committed
    automatically for you when the block exits.

    For example:

    with data as c:
        c.execute("SELECT * FROM data WHERE thing = ?", (thing,))

    Don't try to do any other kind of access, this is a relational database
    and that won't work.

    You can specify the filename as ":memory:" if you want an in-memory
    database.

    More info: http://docs.python.org/2/library/sqlite3.html
    """

    context_mutex = Lock()
    _context_guarded = False

    cur = None

    def __init__(self, filename):
        self.logger = getLogger("Data")
        if filename == ":memory:":
            pass
        else:
            filename = filename.strip("..")

            folders = filename.split("/")
            folders.pop()
            folders = "/".join(folders)

            if not os.path.exists(folders):
                os.makedirs(folders)

            if not os.path.exists(filename):
                open(filename, "w").close()

        self.filename = filename

        self.conn = sqlite3.connect(self.filename)

    def __enter__(self):
        with self.context_mutex:
            self.cur = self.conn.cursor()
            return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.cur.close()
        self._context_guarded = False
        if exc_type is None:
            return True
        return False

    def __str__(self):
        return "<Ultros SQLite data handler: %s>" % self.filename

    def __nonzero__(self):
        return True