__author__ = 'Sean'


class Channel(object):

    name = ""

    def __init__(self, name, protocol=None):
        self.name = name
        self.protocol = protocol

    def respond(self, message):
        raise NotImplementedError("This method must be overridden")
