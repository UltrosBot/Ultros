__author__ = 'Sean'


class Channel(object):
    def __init__(self):
        self.protocol = None

    def respond(self, message):
        raise NotImplemented("This method must be overridden")
