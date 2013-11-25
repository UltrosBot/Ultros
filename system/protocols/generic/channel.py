__author__ = 'Sean'


class Channel(object):

    name = ""

    def __init__(self, protocol=None):
        self.protocol = protocol

    def respond(self, message):
        raise NotImplementedError("This method must be overridden")
