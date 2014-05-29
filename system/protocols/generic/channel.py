__author__ = 'Sean'

from system.translations import Translations
_ = Translations().get()


class Channel(object):

    name = ""

    def __init__(self, name, protocol=None):
        self.name = name
        self.protocol = protocol

    def respond(self, message):
        raise NotImplementedError(_("This method must be overridden"))
