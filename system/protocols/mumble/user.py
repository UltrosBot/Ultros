# coding=utf-8
from system.protocols.generic.channel import Channel
from system.protocols.mumble.acl import Perms

__author__ = 'Sean'

from system.protocols.generic import user


class User(user.User):
    def __init__(self, protocol, session, name, channel, mute, deaf,
                 suppress, self_mute, self_deaf, priority_speaker, recording):
        # Mumble is always "tracked"
        super(User, self).__init__(name, protocol, True)
        self.session = session
        self.channel = channel
        self.mute = mute
        self.deaf = deaf
        self.suppress = suppress
        self.self_mute = self_mute
        self.self_deaf = self_deaf
        self.priority_speaker = priority_speaker
        self.recording = recording

    def __str__(self):
        return "%s (%s)" % (self.nickname, self.session)

    def respond(self, message):
        message = message.replace("{CHARS}", self.protocol.control_chars)
        self.protocol.send_msg(self, message, target_type="user")

    # region permissions
    # Note: Not in a separate class, as in most cases it'd just end up as a
    # tightly coupled mess, and there aren't a whole lot of things you can
    # actually make generic between protocols anyway.

    def can_kick(self, user, channel):
        # TODO: Look into how permissions work properly? It looks like you need
        # kick in the root channel to kick
        return self.protocol.has_permission(0, Perms.KICK)

    def can_ban(self, user, channel):
        # TODO: See TODO in can_kick
        # TODO: This doesn't work - need to look into how permissions work more
        # closely
        return self.protocol.has_permission(0, Perms.BAN)

    # endregion
