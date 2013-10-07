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
        filename = filename.strip("../")
        filename = filename.strip("/..")
        filename = filename.strip("..")
        self.filename = "config/" + filename
        if not os.path.exists("config"):
            self.logger.debug("Creating config directory..")
            os.mkdir("config")
            self.logger.error("Configuration directory not found!")
            self.logger.info("I have created the directory for you, but it's "
                             "empty. Please redownload the example configs "
                             "from https://github.com/McBlockitHelpbot/Ultros "
                             "and set them up before running the bot again.")
            self.logger.info("Expect to see lots of errors scroll by now, and "
                             "for the bot to quit.")
            self.exists = False
            return
        if not os.path.isdir("config"):
            self.logger.debug("Renaming invalid config dir and creating a new "
                              "one")
            os.rename("config", "config_")
            os.mkdir("config")
            self.logger.error("Configuration directory not found!")
            self.logger.info("I have created the directory for you, but it's "
                             "empty. Please redownload the example configs "
                             "from https://github.com/McBlockitHelpbot/Ultros "
                             "and set them up before running the bot again.")
            self.logger.info("Expect to see lots of errors scroll by now, and "
                             "for the bot to quit.")
            self.exists = False
            return
        # Some sanitizing here to make sure people can't escape the config dirs
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
