# coding=utf-8

"""
The storage manager itself

This is in charge of keeping track of all data and config files that
are used throughout the bot. If you're not using this for that, you're doing
it wrong.

Submit an issue or pull request if you need some other kind of storage
format.
"""
from utils.strings import to_filename

__author__ = 'Gareth Coles'

import system.storage.files as files

from system.storage.exceptions import UnknownStorageTypeError
from system.singleton import Singleton
from system.logging.logger import getLogger

from system.translations import Translations
_ = Translations().get()


class StorageManager(object):
    """
    Centralised data and configuration storage and access.
    """

    __metaclass__ = Singleton

    conf_path = ""
    data_path = ""

    config_files = {}
    data_files = {}

    editors = []

    editor_warning = False

    def __init__(self, conf_path="config/", data_path="data/"):
        self.conf_path = conf_path
        self.data_path = data_path

        self.log = getLogger("Storage")

    def get_file(self, obj, storage_type, file_format, path, *args, **kwargs):
        """
        Get the instance of a storage file, creating it if it doesn't exist.

        :param obj: The object requesting access to the file, usually *self*
        :param storage_type: The type of storage file - "data" or "config"
        :param file_format: The file format, as defined in formats.py
        :param path: The path to the file, this also acts as the file's
            identifier
        :param args: Arguments to pass to the file's constructor
        :param kwargs: Keyword arguments to pass to the file's constructor

        :return: The storage file
        """

        path = to_filename(path)

        if ".." in path:
            path = path.replace("..", ".")

        if storage_type == "data":
            if path in self.data_files:
                return self.data_files[path].get()

            storage_file = files.DataFile(file_format, path, self.data_path,
                                          self.__class__, *args, **kwargs)
            storage_file.set_owner(self, obj)
            storage_file.make_ready(self)
            storage_file.load()

            self.data_files[path] = storage_file

            return storage_file.get()

        elif storage_type == "config":
            if path in self.config_files:
                return self.config_files[path].get()

            storage_file = files.ConfigFile(file_format, path, self.conf_path,
                                            self.__class__, *args, **kwargs)
            storage_file.set_owner(self, obj)
            storage_file.make_ready(self)
            storage_file.load()

            self.config_files[path] = storage_file

            return storage_file.get()

        else:
            raise UnknownStorageTypeError(_("Unknown storage type: %s")
                                          % storage_type)

    def release_file(self, obj, storage_type, path):
        """
        When you're done with a file, you should release it here.

        Please only do this if your object actually owns the file.

        :param obj: The object requesting access to the file, usually *self*
        :param storage_type: The type of storage file - "data" or "config"
        :param path: The path to the file, this also acts as the file's
            identifier

        :return: Whether the file existed to be unloaded
        """

        if ".." in path:
            path = path.replace("..", ".")

        if storage_type == "data":
            if path in self.data_files:
                self.data_files[path].release(self)
                del self.data_files[path]
                return True
            return False

        elif storage_type == "config":
            if path in self.config_files:
                self.config_files[path].release(self)
                del self.config_files[path]
                return True
            return False

        else:
            raise UnknownStorageTypeError(_("Unknown storage type: %s")
                                          % storage_type)

    def release_files(self, instance):
        """
        Release all loaded files for an instance.

        :param instance: Instance to release files from
        """

        for key in self.config_files.keys():
            self.log.trace(_("Checking config file: %s") % key)
            f = self.config_files[key]
            if f.is_owner(instance):
                self.log.trace(_("Obj %s owns this file.") % instance)
                f.release(self)
                del self.config_files[key]

        for key in self.data_files.keys():
            self.log.trace(_("Checking data file: %s") % key)
            f = self.data_files[key]
            if f.is_owner(instance):
                self.log.trace(_("Obj %s owns this file.") % instance)
                f.release(self)
                del self.data_files[key]
