# coding=utf-8
__author__ = 'Sean'

from system.protocols.generic import user
from system.protocols.irc.channel import Channel

from system.translations import Translations
_ = Translations().get()


class User(user.User):
    def __init__(self, protocol, nickname, ident=None, host=None,
                 realname=None, is_oper=False, is_tracked=False):
        super(User, self).__init__(nickname, protocol, is_tracked)
        self.ident = ident
        self.host = host
        self.realname = realname
        self.is_oper = is_oper
        self.channels = set()
        self._ranks = {}

    @property
    def fullname(self):
        return "%s!%s@%s" % (self.nickname, self.ident, self.host)

    def __str__(self):
        return self.nickname

    def add_channel(self, channel):
        self.channels.add(channel)

    def remove_channel(self, channel):
        try:
            self.channels.remove(channel)
        except KeyError:
            self.protocol.log.debug(
                _("Tried to remove non-existent channel \"%s\" from user "
                  "\"%s\"")
                % (channel, self))

    def get_ranks_in_channel(self, channel):
        if isinstance(channel, Channel):
            channel = channel.name
        channel = self.protocol.utils.lowercase_nick_chan(channel)
        try:
            return set(self._ranks[channel])
        except KeyError:
            return []

    def get_highest_rank_in_channel(self, channel):
        ranks = self.get_ranks_in_channel(channel)
        highest_rank = None
        for rank in ranks:
            if rank["order"] > highest_rank:
                highest_rank = rank
        return highest_rank

    def add_rank_in_channel(self, channel, rank):
        if isinstance(channel, Channel):
            channel = channel.name
        channel = self.protocol.utils.lowercase_nick_chan(channel)
        if channel not in self._ranks:
            self._ranks[channel] = set()
        self._ranks[channel].add(rank)

    def remove_rank_in_channel(self, channel, rank):
        if isinstance(channel, Channel):
            channel = channel.name
        channel = self.protocol.utils.lowercase_nick_chan(channel)
        try:
            self._ranks[channel].remove(rank)
        except KeyError:
            # Note: This can be thrown either by the dict lookup or the set
            # - remove()
            pass

    def respond(self, message):
        message = message.replace("{CHARS}", self.protocol.control_chars)
        self.protocol.send_msg(self, message, target_type="user")
