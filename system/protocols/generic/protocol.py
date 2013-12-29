# coding=utf-8
__author__ = "Gareth Coles"

from twisted.internet import protocol


class Protocol(protocol.Protocol):
    """
    Base class for building protocols.

    You'll /HAVE/ to subclass this in some form or any protocols you make will
    be invalid without it.

    This class provides several methods that must be uniform across all
    protocols. The reason for this is mostly so plugins that are agnostic
    towards protocols can still work with every protocol the bot is using.

    If you need to inherit another base class (for example irc.IRCClient),
    then use multiple inheritance, with the other base class first.

    For example:
        class Protocol(irc.IRCClient, generic.protocol.Protocol):
            pass

    These are the functions and variables provided by this class that you
    do NOT have to override:
        - factory: The factory for the protocol
        - config: Configuration handler
        - log: Logger
        - event_manager: The event manager
        - command_manager: The command manager

    These ones you should override, but are optional:
        - get_channel(self, channel):
              Only for protocols that handle channels, this is for retrieving
              a channel object. Don't worry about this if you don't use
              channels in your protocol, but always implement it if you do.

    And these you'll absolutely have to override for your protocol to work
    as expected:
        - __version__: The version string
        - name: A string. This is the name of your protocol.
        - nickname: The bot's username or nickname
        - ourselves: A User object describing the bot

        - __init__(self, factory, config)::
              This is where all the setup for your protocol is done, and you
              should also connect it to a service when you do this. Remember
              to set your factory, config, log, event_manager and
              command_manager objects here too.
        - shutdown(self):
              This is called when the protocol needs to be disconnected. You
              should disconnect cleanly and do any cleanup you need to do here.
        - get_user(self, user):
              This is for retrieving a user object. This should always be
              implemented, in every protocol, but it's okay to return None
              if you couldn't find a user object.
    """

    __version__ = ""

    TYPE = "generic"

    factory = None
    config = None
    log = None
    event_manager = None
    command_manager = None

    nickname = ""
    ourselves = None

    def __init__(self, name, factory, config):
        self.name = name
        self.factory = factory
        self.config = config

    def shutdown(self):
        """
        Called when a protocol needs to disconnect. Cleanup should be done
        here.
        """
        self.transport.loseConnection()
        raise NotImplementedError("This function needs to be implemented!")

    def get_user(self, user):
        """
        Used to retrieve a user. Return None if we can't find it.
        :param user: string representing the user we need.
        """
        raise NotImplementedError("This function needs to be implemented!")

    def send_msg(self, target, message, target_type=None, use_event=True):
        """
        Send a message to a user or a channel.
        :param target: A string, User or Channel object.
        :param message: The message to send.
        :param target_type: The type of target - this won't be needed by all
            protocols.
        :param use_event: Whether to fire the MessageSent event or not.
        :return: Boolean describing whether the target was found and messaged.
        """
        raise NotImplementedError("This function needs to be implemented.")


class ChannelsProtocol(Protocol):
    """
    Base protocol for protocols that support channels.
    You'll need to override everything in here as well.
    """

    def get_channel(self, channel):
        """
        Used to retrieve a channel. Return None if we can't find it.
        You don't need to implement this if your protocol doesn't use channels.
        :param channel: string representing the channel we need.
        """
        raise NotImplementedError("This function needs to be implemented!")


class NoChannelsProtocol(Protocol):
    """
    Base protocol for protocols that don't support channels.
    """
