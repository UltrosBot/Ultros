# coding=utf-8
__author__ = 'Sean'

from system.protocols.generic import channel


class Channel(channel.Channel):
    def __init__(self, protocol, name):
        self.protocol = protocol
        self.name = name
        self.users = set()

    def __str__(self):
        return self.name

    def add_user(self, user):
        self.users.add(user)

    def remove_user(self, user):
        try:
            self.users.remove(user)
        except KeyError:
            # According to PEP8, this is easier to read on three lines >_>
            self.protocol.log.debug(
                "Tried to remove non-existent user \"%s\" from channel \"%s\""
                % (user, self))
