__author__ = 'Sean'

from system.translations import Translations
_ = Translations().get()


class User(object):

    authorized = False
    auth_name = ""

    def __init__(self, nickname, protocol=None, is_tracked=False):
        self.nickname = nickname
        self.protocol = protocol
        self.is_tracked = is_tracked

    def respond(self, message):
        raise NotImplementedError(_("This method must be overridden"))
