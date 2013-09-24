# coding=utf-8
__author__ = "Gareth Coles"

from utils.log import getLogger, open_log, close_log


class Channel(object):

    users = []
    modes = {}

    def __init__(self, irc, name):
        self.name = name
        open_log("irc/channels/%s" % name)
        self.irc = irc
        self.logger = getLogger("IRC", "irc/channels/%s" % name,
                                "%(asctime)s | %(name)8s | " + name + " | %(message)s",
                                "%d/%m %H:%M:%S")

    def __del__(self):
        close_log("irc/channels/%s" % self.name)

    def message(self, message):
        pass

    def notice(self, message):
        pass

    def ctcp(self, prefix, data):
        pass