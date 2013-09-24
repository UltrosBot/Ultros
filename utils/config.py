# coding=utf-8
__author__ = "Gareth Coles"

import yaml
import logging

from utils.misc import output_exception


class Config(object):

    data = {}

    def __init__(self, filename):
        self.logger = logging.getLogger("Config")
        self.filename = filename
        self.reload()

    def reload(self):
        try:
            self.fh = open(self.filename, "r")
        except Exception:
            output_exception(self.logger, logging.ERROR)
        else:
            self.data = yaml.safe_load(self.fh)

    def __getitem__(self, y):
        return self.data.__getitem__(y)

    # def __setitem__(self, key, value):
    #     return self.data.__setitem__(key, value)
    #
    # def __setattr__(self, key, value):
    #     return self.data.__setattr__(key, value)