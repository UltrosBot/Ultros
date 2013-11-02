    # coding=utf-8
__author__ = 'Sean'

from system.protocols.generic import user


class User(user.User):
    def __init__(self, protocol, nickname, ident, host):
        self.protocol = protocol
        self.nickname = nickname
        self.host = host
        self.channels = set()

    def __str__(self):
        return self.name

    def add_channel(self, channel):
        self.channels.add(channel)

    def remove_channel(self, channel):
        try:
            self.channels.remove(channel)
        except KeyError:
            self.protocol.log.debug(
                "Tried to remove non-existent channel \"%s\" from user \"%s\""
                % (channel, self))
