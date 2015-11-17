from system.translations import Translations

__author__ = 'Sean'

_ = Translations().get()


class Channel(object):

    name = ""
    users = None

    def __init__(self, name, protocol=None):
        self.name = name
        self.protocol = protocol
        self.users = set()

    def respond(self, message):
        raise NotImplementedError(_("This method must be overridden"))

    def add_user(self, user):
        self.users.add(user)

    def remove_user(self, user):
        try:
            self.users.remove(user)
        except KeyError:
            self.protocol.log.debug(
                "Tried to remove non-existent user \"%s\" from channel \"%s\""
                % (user, self)
            )
