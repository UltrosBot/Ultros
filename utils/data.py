# coding=utf-8
__author__ = "Gareth Coles"

import yaml
#import logging
import os

#from utils.misc import output_exception
from utils.log import getLogger


class Data(object):

    def __init__(self, filename):
        self.logger = getLogger("Data")
        filename = filename.strip("..")
        filename = "data/" + filename
        if not os.path.exists("data"):
            self.logger.debug("Creating data directory..")
            os.mkdir("data")
        if not os.path.isdir("data"):
            self.logger.debug("Renaming invalid data dir and creating a new "
                              "one..")
            os.rename("data", "data_")
            os.mkdir("data")
        self.fh = open(filename, "rw")
        self.data = yaml.safe_load(self.fh)

    def __getitem__(self, y):
        return self.data.__getitem__(y)

    def __getattr__(self, item):
        return self.data.__getattr__(item)

    __getattribute__ = __getattr__

    def __setitem__(self, key, value):
        result = self.data.__setitem__(key, value)
        yaml.dump(self.data, self.fh)
        return result

    def __setattr__(self, key, value):
        result = self.data.__setattr__(key, value)
        yaml.dump(self.data, self.fh)
        return result
