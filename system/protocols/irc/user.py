# coding=utf-8
__author__ = 'Sean'

from system.protocols.generic import user


class User(user.User):
    def __init__(self, protocol, nickname, ident=None, host=None,
                 realname=None, valid=False):
        self.protocol = protocol
        self.nickname = nickname
        self.ident = ident
        self.host = host
        self.realname = realname
        self.valid = valid
        self.channels = set()

    @property
    def fullname(self):
        return "%s!%s@%s" % (self.nickname, self.ident, self.host)

    def __str__(self):
        return self.fullname

    def add_channel(self, channel):
        self.channels.add(channel)

    def remove_channel(self, channel):
        try:
            self.channels.remove(channel)
        except KeyError:
            self.protocol.log.debug(
                "Tried to remove non-existent channel \"%s\" from user \"%s\""
                % (channel, self))
