# coding=utf-8
from system.protocols.generic import user

__author__ = 'Sean'


class User(user.User):
    def __init__(self, protocol, session, name, channel, mute, deaf,
                 suppress, self_mute, self_deaf, priority_speaker, recording):
        self.protocol = protocol
        self.session = session
        self.name = name
        self.channel = channel
        self.mute = mute
        self.deaf = deaf
        self.suppress = suppress
        self.self_mute = self_mute
        self.self_deaf = self_deaf
        self.priority_speaker = priority_speaker
        self.recording = recording

    def __str__(self):
        return u"%s (%s)" % (self.name, self.session)
