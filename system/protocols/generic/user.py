__author__ = 'Sean'


class User(object):
    def __init__(self):
        self.protocol = None

    def msg(self, message):
        raise NotImplementedError("This method must be overridden")

    # TODO: Should these be named some other way to differentiate between
    # - functions plugins should use and internal use ones like these?
    def add_channel(self, channel):
        raise NotImplementedError("This method must be overridden")

    def remove_channel(self, channel):
        raise NotImplementedError("This method must be overridden")
