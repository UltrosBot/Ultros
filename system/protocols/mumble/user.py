# coding=utf-8
__author__ = 'Sean'


class User(object):
    def __init__(self, name, channel_id, mute, deaf, suppress, self_mute,
                 self_deaf, recording):
        self.name = name
        self.channel_id = channel_id
        self.mute = mute
        self.deaf = deaf
        self.suppress = suppress
        self.self_mute = self_mute
        self.self_deaf = self_deaf
        self.recording = recording
