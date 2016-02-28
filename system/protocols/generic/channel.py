# coding=utf-8

from system.translations import Translations

__author__ = 'Sean'

_ = Translations().get()


class Channel(object):
    """
    A channel - Represents a channel on a protocol. Subclass this!

    @ivar name The name of the channel
    @ivar users A set containing all the User objects in the channel
    """

    def __init__(self, name, protocol=None):
        """
        Initialise the channel. Remember to call super in subclasses!

        :arg name: The name of the channel
        :type name: str

        :arg protocol: The protocol object this channel belongs to
        :type protocol: Protocol
        """

        self.name = name  # This is essential!
        self.protocol = protocol  # May be None for one-off or fake channels
        self.users = set()  # This is also essential!

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

    def __json__(self):  # TODO
        """
        Return a representation of your object that can be json-encoded

        For example, a dict, or a JSON string that represents the data in
        the object
        """

        raise NotImplementedError("This method must be overridden")
