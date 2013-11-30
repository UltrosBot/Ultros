__author__ = 'Sean'


class User(object):

    authorized = False
    auth_name = ""

    def __init__(self, protocol=None, is_tracked=False):
        self.protocol = protocol
        self.is_tracked = is_tracked

    def msg(self, message):
        raise NotImplementedError("This method must be overridden")

    # TODO: Should these be named some other way to differentiate between
    # - functions plugins should use and internal use ones like these?

    def respond(self, message):
        raise NotImplementedError("This method must be overridden")
