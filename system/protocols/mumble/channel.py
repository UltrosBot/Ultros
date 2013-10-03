__author__ = 'Sean'


class Channel(object):
    def __init__(self, channel_id, name, parent=None):
        self.channel_id = channel_id
        self.name = name
        self.parent = parent
