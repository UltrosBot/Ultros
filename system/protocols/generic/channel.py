from system.translations import Translations

__author__ = 'Sean'

_ = Translations().get()


class Channel(object):

    name = ""
    users = set()

    def __init__(self, name, protocol=None):
        self.name = name
        self.protocol = protocol
        self.users = set()

    def respond(self, message):
        raise NotImplementedError(_("This method must be overridden"))
