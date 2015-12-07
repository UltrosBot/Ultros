# coding=utf-8

"""
Events specific to Mumble-based protocols
"""

__author__ = 'Gareth Coles'

from system.events.base import BaseEvent


class MumbleEvent(BaseEvent):
    """
    A Mumble event. This will only be thrown from the Mumble protocol.
    If an event subclasses this, chances are it's a Mumble event.
    """

    def __init__(self, caller):
        super(MumbleEvent, self).__init__(caller)


class Reject(MumbleEvent):
    """
    A reject - Sent when we aren't able to connect to a server
    """

    type = ""
    reason = ""

    def __init__(self, caller, typ, reason):
        """
        Initialise the event object.
        """

        self.type = typ
        self.reason = reason

        super(Reject, self).__init__(caller)


class CodecVersion(MumbleEvent):
    """
    Codec version message
    """
    # TODO: Update this docstring when we know what this is for

    alpha = ""
    beta = ""
    prefer_alpha = False
    opus = ""

    def __init__(self, caller, alpha, beta, prefer_alpha, opus):
        """
        Initialise the event object.
        """

        self.alpha = alpha
        self.beta = beta
        self.prefer_alpha = prefer_alpha
        self.opus = opus

        super(CodecVersion, self).__init__(caller)


class CryptoSetup(MumbleEvent):
    """
    Crypto setup message
    """
    # TODO: Update this docstring when we know what this is for

    key = ""
    client_nonce = ""
    server_nonce = ""

    def __init__(self, caller, key, client_n, server_n):
        """
        Initialise the event object.
        """

        self.key = key
        self.client_nonce = client_n
        self.server_nonce = server_n

        super(CryptoSetup, self).__init__(caller)


class PermissionsQuery(MumbleEvent):
    """
    Permissions query - Sent when.. we query permissions?
    """
    # TODO: Update this docstring when we know what this is for

    channel = None
    permissions = ""
    flush = ""

    def __init__(self, caller, channel, permissions, flush):
        """
        Initialise the event object.
        """

        self.channel = channel
        self.permissions = permissions
        self.flush = flush

        super(PermissionsQuery, self).__init__(caller)


class ServerSync(MumbleEvent):
    """
    Server sync message - Sent when we connect to the server
    """

    session = ""
    max_bandwidth = ""
    permissions = ""
    welcome_text = ""

    def __init__(self, caller, session, max_bandwidth, welcome_text,
                 permissions):
        """
        Initialise the event object.
        """

        self.session = session
        self.max_bandwidth = max_bandwidth
        self.welcome_text = welcome_text
        self.permissions = permissions

        super(ServerSync, self).__init__(caller)


class ServerConfig(MumbleEvent):
    """
    Server config message
    """
    # TODO: Update this docstring when we know what this is for

    max_bandwidth = ""
    welcome_text = ""
    allow_html = True
    message_length = 0
    image_message_length = 0

    def __init__(self, caller, max_bandwidth, welcome_text, allow_html,
                 message_length, image_message_length):
        """
        Initialise the event object.
        """

        self.max_bandwidth = max_bandwidth
        self.welcome_text = welcome_text
        self.allow_html = allow_html
        self.message_length = message_length
        self.image_message_length = image_message_length

        super(ServerConfig, self).__init__(caller)


class Ping(MumbleEvent):
    """
    A ping, I guess
    """

    timestamp = ""
    good = 0
    late = 0
    lost = 0
    resync = 0
    tcp = 0
    udp = 0
    tcp_avg = 0
    udp_avg = 0
    tcp_var = 0
    udp_var = 0

    def __init__(self, caller, timestamp, good, late, lost, resync, tcp, udp,
                 tcp_avg, udp_avg, tcp_var, udp_var):
        """
        Initialise the event object.
        """

        self.timestamp = timestamp
        self.good = good
        self.late = late
        self.lost = lost
        self.resync = resync
        self.tcp = tcp
        self.udp = udp
        self.tcp_avg = tcp_avg
        self.udp_avg = udp_avg
        self.tcp_var = tcp_var
        self.udp_var = udp_var

        super(Ping, self).__init__(caller)


class UserRemove(MumbleEvent):
    """
    User removal message

    It looks like this is fired under three conditions..

    * When a user disconnects or loses connection

        * *kicker* will be None in that case

    * When a user is kicked

        * *kicker* will be set and ban will be False

    * When a user is banned

        * *kicker* will be set and ban will be True

    This still requires some more research, the Mumble docs are awful.
    """
    # TODO: Update this docstring when we're more sure of it

    session = ""  # Session ID
    actor = ""  # Session ID
    user = None  # User object
    kicker = None  # User object
    reason = ""  # Reason
    ban = False  # True if banned, false if kicked

    def __init__(self, caller, session, actor, user, reason, ban, kicker):
        """
        Initialise the event object.
        """

        self.caller = caller
        self.session = session
        self.actor = actor
        self.user = user
        self.reason = reason
        self.ban = ban
        self.kicker = kicker

        super(UserRemove, self).__init__(caller)


class Unknown(MumbleEvent):
    """
    Unknown message - Called when we get a message that isn't already
    handled
    """

    type = ""
    message = None

    def __init__(self, caller, typ, message):
        """
        Initialise the event object.
        """

        self.type = typ
        self.message = message

        super(Unknown, self).__init__(caller)


class UserJoined(MumbleEvent):
    """
    User join - Sent when a user joins the server
    """

    user = None

    def __init__(self, caller, user):
        """
        Initialise the event object.
        """

        self.user = user

        super(UserJoined, self).__init__(caller)


class UserMoved(MumbleEvent):
    """
    User moved - Sent when a user moves channel, or is moved

    This is also fired when a user connects.
    """

    user = None
    channel = None
    old_channel = None

    def __init__(self, caller, user, channel, old):
        """
        Initialise the event object.
        """

        self.user = user
        self.channel = channel
        self.old_channel = old

        super(UserMoved, self).__init__(caller)


class UserStateToggleEvent(MumbleEvent):
    """
    Base class for events that are simply user state toggles

    Don't use this directly; inherit it!
    """

    user = None
    state = False
    actor = None

    def __init__(self, caller, user, state, actor=None):
        """
        Initialise the event object.
        """

        self.user = user
        self.state = state
        self.actor = actor

        super(UserStateToggleEvent, self).__init__(caller)


class UserMuteToggle(UserStateToggleEvent):
    """
    User mute toggle - Sent when a user is muted or unmuted (but not by
    themselves)

    state: True if muted, False if unmuted
    """

    pass


class UserDeafToggle(UserStateToggleEvent):
    """
    User deaf toggle - Sent when a user is deafened or undeafened (but not
    by themselves)

    state: True if deafened, False if undeafened
    """

    pass


class UserSuppressionToggle(UserStateToggleEvent):
    """
    User suppression toggle - Sent when a user is suppressed or
    unsuppressed

    state: True if suppressed, False if unsuppressed
    """

    pass


class UserSelfMuteToggle(UserStateToggleEvent):
    """
    User mute toggle - Sent when a user is muted or unmuted by
    themselves

    state: True if muted, False if unmuted
    """

    pass


class UserSelfDeafToggle(UserStateToggleEvent):
    """
    User deaf toggle - Sent when a user is deafened or undeafened by
    themselves

    state: True if deafened, False if undeafened
    """

    pass


class UserPrioritySpeakerToggle(UserStateToggleEvent):
    """
    Priority speaker toggle - Sent when a user is set as priority speaker

    state: True if set, False if unset
    """

    pass


class UserRecordingToggle(UserStateToggleEvent):
    """
    Recording toggle - Sent when a user starts or stops recording

    state: True if started, False if stopped
    """

    pass


class UserStats(MumbleEvent):
    """
    User stats updated

    user: User whose stats have been updated
    """

    def __init__(self, caller, user):
        """
        Initialise the event object.
        """

        self.user = user

        super(UserStats, self).__init__(caller)


class UserRegisteredEvent(MumbleEvent):
    """
    Base class for user [un]registered events

    Don't use this directly; inherit it!
    """

    def __init__(self, caller, user, user_id, actor):
        """
        Initialise the event object.
        """

        self.user = user
        self.user_id = user_id
        self.actor = actor

        super(UserRegisteredEvent, self).__init__(caller)


class UserRegistered(UserRegisteredEvent):
    """
    User registered

    user: User who has been registered
    user_id: User's new ID
    actor: User who registered `user`
    """


class UserUnregistered(UserRegisteredEvent):
    """
    User unregistered

    user: User who has been unregistered
    user_id: User's old ID
    actor: User who unregistered `user`
    """


class ChannelCreated(MumbleEvent):
    """
    New channel - Sent when a channel is created
    """

    channel = None

    def __init__(self, caller, channel):
        """
        Initialise the event object.
        """

        self.channel = channel

        super(ChannelCreated, self).__init__(caller)


class ChannelLinked(MumbleEvent):
    """
    Channel link added - Sent when two channels are linked together
    """

    from_channel = None
    to_channel = None

    def __init__(self, caller, from_, to_):
        """
        Initialise the event object.
        """

        self.from_channel = from_
        self.to_channel = to_

        super(ChannelLinked, self).__init__(caller)


class ChannelUnlinked(MumbleEvent):
    """
    Channel link removed - Sent when two channels have their link removed
    """

    from_channel = None
    to_channel = None

    def __init__(self, caller, from_, to_):
        """
        Initialise the event object.
        """

        self.from_channel = from_
        self.to_channel = to_

        super(ChannelUnlinked, self).__init__(caller)
