"""Events specific to IRC-based protocols"""

__author__ = 'Gareth Coles'

from system.events.base import BaseEvent


class IRCEvent(BaseEvent):
    """An IRC event. This will only be thrown from the IRC protocol.
    If an event subclasses this, chances are it's an IRC event.
    """

    def __init__(self, caller):
        super(IRCEvent, self).__init__(caller)


class MOTDReceivedEvent(IRCEvent):
    """Thrown when the MOTD is received"""

    motd = ""

    def __init__(self, caller, motd):
        """Initialise the event object."""

        self.motd = motd
        super(MOTDReceivedEvent, self).__init__(caller)


class ChannelJoinedEvent(IRCEvent):
    """Thrown when we join a channel"""

    channel = None

    def __init__(self, caller, channel):
        """Initialise the event object."""

        self.channel = channel
        super(ChannelJoinedEvent, self).__init__(caller)


class ChannelPartedEvent(IRCEvent):
    """Thrown when we part a channel"""

    channel = None

    def __init__(self, caller, channel):
        """Initialise the event object."""

        self.channel = channel
        super(ChannelPartedEvent, self).__init__(caller)


class KickedEvent(IRCEvent):
    """Thrown when we get kicked from a channel"""

    channel = None
    kicker = None
    message = ""

    def __init__(self, caller, channel, kicker, message):
        """Initialise the event object."""

        self.channel = channel
        self.kicker = kicker
        self.message = message
        super(KickedEvent, self).__init__(caller)


class UserJoinedEvent(IRCEvent):
    """Thrown when someone joins a channel we're in"""

    channel = None
    user = None

    def __init__(self, caller, channel, user):
        """Initialise the event object."""

        self.channel = channel
        self.user = user
        super(UserJoinedEvent, self).__init__(caller)


class UserPartedEvent(IRCEvent):
    """Thrown when someone parts a channel we're in"""

    channel = None
    user = None

    def __init__(self, caller, channel, user):
        """Initialise the event object."""

        self.channel = channel
        self.user = user
        super(UserPartedEvent, self).__init__(caller)


class UserKickedEvent(IRCEvent):
    """Thrown when someone is kicked from a channel we're in"""

    channel = None
    user = None
    kicker = None
    reason = ""

    def __init__(self, caller, channel, user, kicker, reason):
        """Initialise the event object."""

        self.channel = channel
        self.user = user
        self.kicker = kicker
        self.reason = reason
        super(UserKickedEvent, self).__init__(caller)


class CTCPQueryEvent(IRCEvent):
    """Thrown when we receive a CTCP query"""

    user = None
    channel = None
    action = ""
    data = ""

    def __init__(self, caller, user, channel, action, data):
        """Initialise the event object."""

        self.user = user
        self.channel = channel
        self.action = action
        self.data = data
        super(CTCPQueryEvent, self).__init__(caller)


class UserQuitEvent(IRCEvent):
    """Thrown when a user disconnects from the server - this is thrown BEFORE
    we clean up the user object
    """

    user = None
    message = ""

    def __init__(self, caller, user, message):
        """Initialise the event object."""

        self.user = user
        self.message = message
        super(UserQuitEvent, self).__init__(caller)


class TopicUpdatedEvent(IRCEvent):
    """Thrown when the topic is updated - this includes on channel join!"""

    channel = None
    user = None
    topic = ""

    def __init__(self, caller, channel, user, topic):
        """Initialise the event object."""

        self.channel = channel
        self.user = user
        self.topic = topic
        super(TopicUpdatedEvent, self).__init__(caller)


class WHOReplyEvent(IRCEvent):
    """Thrown when the server sends us a WHO reply chunk - this is essentially
    just populating a user object, but the raw data is also available
    """

    channel = None
    user = None
    data = {}

    def __init__(self, caller, channel, user, data):
        """Initialise the event object."""

        self.channel = channel
        self.user = user
        self.data = data
        super(WHOReplyEvent, self).__init__(caller)


class WHOReplyEndEvent(IRCEvent):
    """Thrown when the server is done sending WHO replies for a channel"""

    channel = None

    def __init__(self, caller, channel):
        """Initialise the event object."""

        self.channel = channel
        super(WHOReplyEndEvent, self).__init__(caller)


class BanListEvent(IRCEvent):
    """Thrown when the server sends us a ban list reply chunk

    It's advisable to wait for the end of the ban list before actioning on
    the ban list because this event is called synchronously, and you don't
    want to lock up the bot.

    Instead, wait for the BanListEndEvent and make your handler for it
    threaded.
    """

    channel = None
    mask = ""
    owner = ""
    when = ""

    def __init__(self, caller, channel, mask, owner, when):
        """Initialise the event object."""

        self.channel = channel
        self.mask = mask
        self.owner = owner
        self.when = when
        super(BanListEvent, self).__init__(caller)


class BanListEndEvent(IRCEvent):
    """Thrown when the server is done sending ban list replies for a channel"""

    channel = None

    def __init__(self, caller, channel):
        """Initialise the event object."""

        self.channel = channel
        super(BanListEndEvent, self).__init__(caller)


class NAMESReplyEvent(IRCEvent):
    """Thrown when the server sends us a NAMES reply chunk"""

    channel = None
    status = ""  # Channel status - @ for secret, * for private
    names = []

    def __init__(self, caller, channel, status, names):
        """Initialise the event object."""

        self.channel = channel
        self.status = status
        self.names = names
        super(NAMESReplyEvent, self).__init__(caller)


class NAMESReplyEndEvent(IRCEvent):
    """Thrown when the server is done sending NAMES replies for a channel"""

    channel = None
    message = ""

    def __init__(self, caller, channel, message):
        """Initialise the event object."""

        self.channel = channel
        self.message = message
        super(NAMESReplyEndEvent, self).__init__(caller)


class InviteOnlyChannelErrorEvent(IRCEvent):
    """Thrown when we are unable to join a channel because it's invite-only

    The channel is a string here as we don't create a channel object for
    channels we weren't able to join.
    """

    channel = ""

    def __init__(self, caller, channel):
        """Initialise the event object."""

        self.channel = channel
        super(InviteOnlyChannelErrorEvent, self).__init__(caller)


class CannotDoCommandErrorEvent(IRCEvent):
    """Thrown when the server is unable to process a command we sent"""

    command = ""
    message = ""

    def __init__(self, caller, command, message):
        """Initialise the event object."""

        self.command = command
        self.message = message
        super(CannotDoCommandErrorEvent, self).__init__(caller)


class ChannelCreationDetailsEvent(IRCEvent):
    """Thrown when we receive the creation details for a channel"""

    channel = None
    user = None
    when = ""

    def __init__(self, caller, channel, user, when):
        """Initialise the event object."""

        self.channel = channel
        self.user = user
        self.when = when
        super(ChannelCreationDetailsEvent, self).__init__(caller)


class LOCALUSERSReplyEvent(IRCEvent):
    """Thrown when the server sends us a LOCALUSERS reply, which is usually on
    connect
    """

    message = ""

    def __init__(self, caller, message):
        """Initialise the event object."""

        self.message = message
        super(LOCALUSERSReplyEvent, self).__init__(caller)


class GLOBALUSERSReplyEvent(IRCEvent):
    """Thrown when the server sends us a GLOBALUSERS reply, which is usually on
    connect
    """

    message = ""

    def __init__(self, caller, message):
        """Initialise the event object."""

        self.message = message
        super(GLOBALUSERSReplyEvent, self).__init__(caller)


class VHOSTSetEvent(IRCEvent):
    """Thrown when we've been assigned a VHOST"""

    vhost = ""
    setter = None

    def __init__(self, caller, vhost, setter):
        """Initialise the event object."""

        self.vhost = vhost
        self.setter = setter
        super(VHOSTSetEvent, self).__init__(caller)


class UnhandledMessageEvent(IRCEvent):
    """Thrown when we receive a message that hasn't been implemented by the IRC
    protocol object yet
    """

    prefix = ""
    command = ""
    params = []

    def __init__(self, caller, prefix, command, params):
        """Initialise the event object."""

        self.prefix = prefix
        self.command = command
        self.params = params
        super(UnhandledMessageEvent, self).__init__(caller)


class PongEvent(IRCEvent):
    """Thrown when we get a PONG from the server. Why did we even implement
    this?
    """

    def __init__(self, caller):
        """Initialise the event object."""

        super(PongEvent, self).__init__(caller)


class InvitedEvent(IRCEvent):
    """Thrown when we get invited to a channel"""

    user = None
    channel = ""
    auto_join = False

    def __init__(self, caller, user, channel, auto_join):
        """Initialise the event object."""

        self.user = user
        self.channel = channel
        self.auto_join = auto_join
        super(InvitedEvent, self).__init__(caller)


class ModeChangedEvent(IRCEvent):
    """Thrown when a mode is changed"""

    user = None
    channel = None
    action = False
    modes = ""
    args = ""

    def __init__(self, caller, user, channel, action, modes, args):
        """Initialise the event object."""

        self.user = user
        self.channel = channel
        self.action = action
        self.modes = modes
        self.args = args
        super(ModeChangedEvent, self).__init__(caller)


class ISUPPORTReplyEvent(IRCEvent):
    """Thrown when we get an ISUPPORT from the server"""

    prefix = ""
    params = []

    def __init__(self, caller, prefix, params):
        """Initialise the event object."""

        self.prefix = prefix
        self.params = params
        super(ISUPPORTReplyEvent, self).__init__(caller)
