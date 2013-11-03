# coding=utf-8
__author__ = "Gareth Coles"

import yaml
import os
import logging

from threading import Lock

from utils.log import getLogger


class Data(object):

    data = {}

    mutex = Lock()

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

        dirpath = filename.split("/")
        dirpath.pop()
        dirpath = "/".join(dirpath)

        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        self.filename = filename
        self.load()

    def load(self):
        with self.mutex:
            if not os.path.exists(self.filename):
                open(self.filename, "w").close()
            fh = open(self.filename, "r")
            self.data = yaml.load(fh)
            fh.close()
            if not self.data:
                self.data = {}

    def save(self):
        with self.mutex:
            data = yaml.dump(self.data)
            fh = open(self.filename, "w")
            fh.write(data)
            fh.flush()
            fh.close()

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
        return "<Ultros data handler: %s>" % self.data