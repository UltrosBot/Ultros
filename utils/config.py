# coding=utf-8
__author__ = "Gareth Coles"

import yaml
import logging
import os

from utils.misc import output_exception
from utils.log import getLogger


class Config(object):
    data = {}
    exists = True
    fh = None

    def __init__(self, filename):
        self.logger = getLogger("Config")
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