__author__ = 'Gareth Coles'

from system.decorators import Singleton
from system.storage.exceptions import OtherOwnershipError, \
    UnknownStorageTypeError

import system.storage.files as files


@Singleton
class StorageManager(object):
    """
    Centralised data and configuration storage and access.
    """

    conf_path = ""
    data_path = ""

    config_files = {}
    data_files = {}

    # DONE: Files should only have one owner.

    def __init__(self, conf_path="config/", data_path="data/"):
        self.conf_path = conf_path
        self.data_path = data_path

    @staticmethod
    def instance(self=None):
        """
        This only exists to help developers using decent IDEs.
        Don't actually use it.
        """
        if self is None:
            self = StorageManager
        return self

    def get_file(self, plugin, storage_type, file_format, path):
        if ".." in path:
            path = path.replace("..", ".")

        if storage_type == "data":
            if path in self.data_files:
                if not self.data_files[path].is_owner(plugin):
                    raise OtherOwnershipError("Data file %s is owned by "
                                              "another plugin." % path)
                return self.data_files[path].get()
            storage_file = files.DataFile(file_format, path, self.data_path,
                                          self.__class__)
            storage_file.set_owner(self, plugin)
            storage_file.make_ready(self)
            storage_file.load()

            self.data_files[path] = storage_file

            return storage_file.get()

        elif storage_type == "config":
            if path in self.config_files:
                if not self.config_files[path].is_owner(plugin):
                    raise OtherOwnershipError("Data file %s is owned by "
                                              "another plugin." % path)
                return self.config_files[path].get()
            storage_file = files.ConfigFile(file_format, path, self.conf_path,
                                            self.__class__)
            storage_file.set_owner(self, plugin)
            storage_file.make_ready(self)
            storage_file.load()

            self.config_files[path] = storage_file

            return storage_file.get()

        else:
            raise UnknownStorageTypeError("Unknown storage type: %s"
                                          % storage_type)
