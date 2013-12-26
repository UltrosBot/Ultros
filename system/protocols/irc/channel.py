# coding=utf-8

__author__ = 'Sean'

from system.protocols.generic import channel


class Channel(channel.Channel):
    def __init__(self, protocol, name):
        super(Channel, self).__init__(name, protocol)
        self.users = set()
        self._modes = {}

    def __str__(self):
        return self.name

    def add_user(self, user):
        self.users.add(user)

    def remove_user(self, user):
        try:
            self.users.remove(user)
        except KeyError:
            #According to PEP8, this is easier to read on two lines <_<
            self.protocol.log.debug(
                "Tried to remove non-existent user \"%s\" from channel \"%s\""
                % (user, self))

    def set_mode(self, mode, arg=None):
        """
        Sets a mode to the channel, along with an optional parameter.
        """
        self._modes[mode] = arg

    def remove_mode(self, mode):
        try:
            del self._modes[mode]
        except KeyError:
            self.protocol.log.debug(
                "Tried to remove non-existent mode \"%s\" from channel \"%s\""
                % (mode, self))

    def get_mode(self, mode):
        """
        Returns the parameter of a mode.
        Throws IndexError if mode doesn't exist.
        """
        return self._modes[mode]

    def has_mode(self, mode):
        return mode in self._modes

    def respond(self, message):
        message = message.replace("{CHARS}", self.protocol.control_chars)
        self.protocol.send_privmsg(self.name, message)
