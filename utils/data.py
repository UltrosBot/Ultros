# coding=utf-8
__author__ = "Gareth Coles"

import yaml
import logging

from utils.misc import output_exception


class Data(object):

    def __init__(self, filename):
        self.logger = logging.getLogger("Data")
        try:
            self.fh = open(filename, "r")
        except Exception:
            output_exception(self.logger, logging.ERROR)
        else:
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