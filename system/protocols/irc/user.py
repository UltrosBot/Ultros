# coding=utf-8
from system.protocols.irc.channel import Channel

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
        self._ranks = {}

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

    def get_rank_in_channel(self, channel):
        if not isinstance(channel, Channel):
            channel = self.protocol.get_channel(channel)
        try:
            return self._ranks[channel]
        except KeyError:
            return None
