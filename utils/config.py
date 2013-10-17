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

        # def __setitem__(self, key, value):
        #     return self.data.__setitem__(key, value)
        #
        # def __setattr__(self, key, value):
        #     return self.data.__setattr__(key, value)
