# coding=utf-8
__author__ = 'Sean'


class User(object):
    def __init__(self, session, name, channel_id, mute, deaf, suppress,
                 self_mute, self_deaf, priority_speaker, recording):
        self.session = session
        self.name = name
        self.channel_id = channel_id
        self.mute = mute
        self.deaf = deaf
        self.suppress = suppress
        self.self_mute = self_mute
        self.self_deaf = self_deaf
        self.priority_speaker = priority_speaker
        self.recording = recording

    def __str__(self):
        return u"%s (%s)" % (self.name, self.session)
