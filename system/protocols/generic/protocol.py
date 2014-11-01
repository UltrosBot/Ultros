# coding=utf-8
__author__ = "Gareth Coles"

from twisted.internet import protocol

from system.decorators.log import deprecated
from system.translations import Translations
_ = Translations().get()


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

    For example::

        class Protocol(irc.IRCClient, generic.protocol.Protocol):
            pass

    These are the functions and variables provided by this class that you
    do NOT have to override:

    * factory: The factory for the protocol
    * config: Configuration handler
    * log: Logger
    * event_manager: The event manager
    * command_manager: The command manager
    * CHANNELS: Don't override this, use one of the relevant subclasses instead

    These ones you should override, but are optional:

    * get_channel(self, channel):

        * Only for protocols that handle channels, this is for retrieving
          a channel object. Don't worry about this if you don't use
          channels in your protocol, but always implement it if you do.

    And these you'll absolutely have to override for your protocol to work
    as expected:

    * Variables

        * __version__: The version string
        * name: A string. This is the name of your protocol.
        * nickname: The bot's username or nickname
        * ourselves: A User object describing the bot

    * Functions

        * __init__(self, factory, config):

            * This is where all the setup for your protocol is done, and you
              should also connect it to a service when you do this. Remember
              to set your factory, config, log, event_manager and
              command_manager objects here too.
            * If you're building a protocol, make sure that it doesn't
              actually connect until reactor.run() is called; you can use
              a call to reactor.callLater(0, startup_function) to do this.

        * shutdown(self):

            * This is called when the protocol needs to be disconnected. You
              should disconnect cleanly and do any cleanup you need to do here.

        * get_user(self, user):

            * This is for retrieving a user object. This should always be
              implemented, in every protocol, but it's okay to return None
              if you couldn't find a user object.

        * send_msg(self, target, message, target_type, use_event):

            * This is a generic abstraction for sending a message. You should
              always implement this. target_type and use_event default to
              None and True respectively and these options should always be
              honored as appropriate.

        * send_action(self, target, message, target_type, use_event):

            * This is a generic abstraction for sending an action (/me on some
              networks). It works much the same as send_msg but should be
              treated with different formatting (For example, on IRC,
              we would send a CTCP ACTION to the target).
    """

    __version__ = ""

    TYPE = "generic"
    CHANNELS = False

    factory = None
    config = None
    log = None
    event_manager = None
    command_manager = None

    nickname = ""
    ourselves = None
    can_flood = False

    control_chars = "."

    def __init__(self, name, factory, config):
        # You don't necessarily need to call the super-class here,
        #   however we do recommend at least copy-pasting the below code
        #   into your __init__.
        # Twisted uses old-style classes, so super() won't work if you intend
        #   on using it!
        self.name = name
        self.factory = factory
        self.config = config
        # Default values for optional main config section
        try:
            self.can_flood = self.config["main"]["can-flood"]
        except KeyError:
            self.can_flood = False

    def shutdown(self):
        """
        Called when a protocol needs to disconnect. Cleanup should be done
        here.
        """

        self.transport.loseConnection()
        raise NotImplementedError(_("This function needs to be implemented!"))

    def get_user(self, user):
        """
        Used to retrieve a user.

        Return None if we can't find it.

        :param user: string representing the user we need.
        """

        raise NotImplementedError(_("This function needs to be implemented!"))

    def global_kick(self, user, reason=None, force=False):
        """
        Attempts to kick a user from the network.

        In many protocols, we can't know if we have permission to kick until
        we do it, and in those cases, this method should always attempt it.

        If a protocol does not support kicking, then it should always return
        False.

        :param user: The user to kick
        :param reason: The reason for the kick
        :param force: Bypass local permissions check
        :return: Whether or not a kick was attempted
        """

        raise NotImplementedError(_("This function needs to be implemented!"))

    def global_ban(self, user, reason=None, force=False):
        """
        Attempts to ban a user from the network.

        In many protocols, we can't know if we have permission to ban until
        we do it, and in those cases, this method should always attempt it.

        If a protocol does not support baning, then it should always return
        False.

        :param user: The user to ban
        :param reason: The reason for the ban
        :param force: Bypass local permissions check
        :return: Whether or not a ban was attempted
        """

        raise NotImplementedError("This function needs to be implemented!")

    def send_msg(self, target, message, target_type=None, use_event=True):
        """
        Send a message to a user or a channel.

        :param target: A string, User or Channel object.
        :param message: The message to send.
        :param target_type: The type of target
        :param use_event: Whether to fire the MessageSent event or not.
        :return: Boolean describing whether the target was found and messaged.
        """

        raise NotImplementedError(_("This function needs to be implemented."))

    def send_action(self, target, message, target_type=None, use_event=True):
        """
        Send an action to a user of channel. (i.e. /me used action!)

        If a protocol does not have a separate method for actions, then this
        method should send a regular message in format "*message*", in italics
        if possible.

        :param target: A string, User or Channel object.
        :param message: The message to send.
        :param target_type: The type of target
        :param use_event: Whether to fire the MessageSent event or not.
        :return: Boolean describing whether the target was found and messaged.
        """

        raise NotImplementedError(_("This function needs to be implemented."))


class ChannelsProtocol(Protocol):
    """
    Base protocol for protocols that support channels.
    You'll need to override everything in here as well.
    """

    CHANNELS = True

    @property
    def num_channels(self):
        raise NotImplementedError(_("This function needs to be implemented!"))

    def get_channel(self, channel):
        """
        Used to retrieve a channel. Return None if we can't find it.

        You don't need to implement this if your protocol doesn't use channels.
        :param channel: string representing the channel we need.
        """

        raise NotImplementedError(_("This function needs to be implemented!"))

    def join_channel(self, channel, password=None):
        """
        Attempts to join a channel.

        An optional password may be provided, which
        should be ignored by protocols that do not support them.
        Return value is whether or not a channel join was attempted - it is not
        a guarantee that the operation will be successful. An example of when
        it could return False is if a channel doesn't exist and can't simply be
        created by joining it.

        :param channel: Channel to join
        :param password: Password for channel
        :return: Whether or not a join was attempted
        """

        raise NotImplementedError(_("This function needs to be implemented!"))

    def leave_channel(self, channel, reason=None):
        """
        Attempts to leave a channel.

        An optional reason may be provided, which
        should be ignored by protocols that do not support them.
        Return value is whether or not a channel leave was attempted - it is
        not a guarantee that the operation will be successful. An example of
        when it could return False is if a protocol requires you to be in a
        channel.

        :param channel: Channel to join
        :param reason: Reason for leaving
        :return: Whether or not a part was attempted
        """

        raise NotImplementedError(_("This function needs to be implemented!"))

    @deprecated("Use `channel_kick` or `global_kick` instead")
    def kick(self, *args, **kwargs):
        """
        Deprecated, please see `channel_kick`
        """

        return self.channel_kick(*args, **kwargs)

    @deprecated("Use `channel_ban` or `global_ban` instead")
    def ban(self, *args, **kwargs):
        """
        Deprecated, please see `channel_ban`
        """

        return self.channel_ban(*args, **kwargs)

    def channel_kick(self, user, channel=None, reason=None, force=False):
        """
        Attempts to kick a user from a channel.

        In many protocols, we can't
        know if we have permission to kick until we do it, and in those cases,
        this method should always attempt it.
        Some protocols may not require a channel (single-channel, for example),
        or may not support giving a reason, in which case, those parameters
        should be ignored.
        If a protocol does not support kicking, then it should always return
        False.

        :param user: The user to kick
        :param channel: The channel to kick from
        :param reason: The reason for the kick
        :param force: Bypass local permissions check
        :return: Whether or not a kick was attempted
        """

        raise NotImplementedError(_("This function needs to be implemented!"))

    def channel_ban(self, user, channel=None, reason=None, force=False):
        """
        Attempts to ban a user from a channel.

        In many protocols, we can't
        know if we have permission to ban until we do it, and in those cases,
        this method should always attempt it.
        Some protocols may not require a channel (single-channel, for example),
        or may not support giving a reason, in which case, those parameters
        should be ignored.
        If a protocol does not support baning, then it should always return
        False.

        :param user: The user to ban
        :param channel: The channel to ban from
        :param reason: The reason for the ban
        :param force: Bypass local permissions check
        :return: Whether or not a ban was attempted
        """

        raise NotImplementedError("This function needs to be implemented!")


class NoChannelsProtocol(Protocol):
    """
    Base protocol for protocols that don't support channels.
    """
