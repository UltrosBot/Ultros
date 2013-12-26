__author__ = 'Sean'


class User(object):

    authorized = False
    auth_name = ""

    def __init__(self, nickname, protocol=None, is_tracked=False):
        self.nickname = nickname
        self.protocol = protocol
        self.is_tracked = is_tracked

    def respond(self, message):
        raise NotImplementedError("This method must be overridden")
