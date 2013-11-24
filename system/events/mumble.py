__author__ = 'Gareth Coles'

from system.events.base import BaseEvent


class MumbleEvent(BaseEvent):
    """
    A Mumble event. This will only be thrown from the Mumble protocol.
    If an event subclasses this, chances are it's a Mumble event.
    """

    def __init__(self, caller):
        super(self.__class__, self).__init__(caller)


class Reject(MumbleEvent):
    """
    A reject - Sent when we aren't able to connect to a server
    """

    type = ""
    reason = ""

    def __init__(self, caller, typ, reason):
        self.type = typ
        self.reason = reason

        super(self.__class__, self).__init__(caller)


class CodecVersion(MumbleEvent):
    """
    Codec version message
    """
    # TODO: Update this docstring when we know what this is for

    version = ""

    def __init__(self, caller, version):
        self.version = version

        super(self.__class__, self).__init__(caller)


class CryptoSetup(MumbleEvent):
    """
    Crypto setup message
    """
    # TODO: Update this docstring when we know what this is for

    client_nonce = ""
    server_nonce = ""

    def __init__(self, caller, client_n, server_n):
        self.client_nonce = client_n
        self.server_nonce = server_n

        super(self.__class__, self).__init__(caller)


class PermissionsQuery(MumbleEvent):
    """
    Permissions query - Sent when.. we query permissions?
    """
    # TODO: Update this docstring when we know what this is for

    channel = None
    permissions = ""
    flush = ""

    def __init__(self, caller, channel, permissions, flush):
        self.channel = channel
        self.permissions = permissions
        self.flush = flush

        super(self.__class__, self).__init__(caller)


class ServerSync(MumbleEvent):
    """
    Server sync message - Sent when we connect to the server.
    """

    session = ""
    bandwidth = ""
    permissions = ""

    def __init__(self, caller, session, bandwidth, permissions):
        self.session = session
        self.bandwidth = bandwidth
        self.permissions = permissions

        super(self.__class__, self).__init__(caller)


class ServerConfig(MumbleEvent):
    """
    Server config message
    """
    # TODO: Update this docstring when we know what this is for

    bandwidth = ""
    allow_html = True
    message_length = 0

    def __init__(self, caller, bandwidth, allow_html, message_length):
        self.bandwidth = bandwidth
        self.allow_html = allow_html
        self.message_length = message_length

        super(self.__class__, self).__init__(caller)


class Ping(MumbleEvent):
    """
    A ping, I guess.
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

        super(self.__class__, self).__init__(caller)


class UserRemove(MumbleEvent):
    """
    User removal message
    """
    # TODO: Update this docstring when we know what this is for

    session = ""
    user = None
    reason = ""
    ban = ""

    def __init__(self, caller, session, actor, reason, ban):
        self.caller = caller
        self.session = session
        self.user = actor
        self.reason = reason
        self.ban = ban

        super(self.__class__, self).__init__(caller)


class Unknown(MumbleEvent):
    """
    Unknown message - Called when we get a message that isn't already handled.
    """

    type = None
    message = ""

    def __init__(self, caller, typ, message):
        self.type = type
        self.message = message

        super(self.__class__, self).__init__(caller)


class UserJoined(MumbleEvent):
    """
    User join - Sent when a user joins the server
    """

    user = None

    def __init__(self, caller, user):
        self.user = user

        super(self.__class__, self).__init__(caller)


class UserMoved(MumbleEvent):
    """
    User moved - Sent when a user moves channel, or is moved
    """

    user = None
    channel = None

    def __init__(self, caller, user, channel):
        self.user = user
        self.channel = channel

        super(self.__class__, self).__init__(caller)


class UserStateToggleEvent(MumbleEvent):
    """
    Base class for events that are simply user state toggles.
    Don't use this directly; inherit it!
    """

    user = None
    state = False

    def __init__(self, caller, user, state):
        self.user = user
        self.state = state

        super(self.__class__, self).__init__(caller)


class UserMuteToggle(UserStateToggleEvent):
    """
    User mute toggle - Sent when a user is muted or unmuted (but not by
        themselves)

    state: True if muted, False if unmuted
    """


class UserDeafToggle(UserStateToggleEvent):
    """
    User deaf toggle - Sent when a user is deafened or undeafened (but not by
        themselves)

    state: True if deafened, False if undeafened
    """


class UserSupressionToggle(UserStateToggleEvent):
    """
    User supression toggle - Sent when a user is surpressed or unsurpressed.

    state: True if surpressed, False if unsurpressed
    """


class UserSelfMuteToggle(UserStateToggleEvent):
    """
    User mute toggle - Sent when a user is muted or unmuted by
        themselves.

    state: True if muted, False if unmuted
    """


class UserSelfDeafToggle(UserStateToggleEvent):
    """
    User deaf toggle - Sent when a user is deafened or undeafened by
        themselves.

    state: True if deafened, False if undeafened
    """


class UserPrioritySpeakerToggle(UserStateToggleEvent):
    """
    Priority speaker toggle - Sent when a user is set as priority speaker.

    state: True if set, False if unset
    """


class UserRecordingToggle(UserStateToggleEvent):
    """
    Recording toggle - Sent when a user starts or stops recording.

    state: True if started, False if stopped
    """


class ChannelCreated(MumbleEvent):
    """
    New channel - Sent when a channel is created.
    """

    channel = None

    def __init__(self, caller, channel):
        self.channel = channel

        super(self.__class__, self).__init__(caller)


class ChannelLinked(MumbleEvent):
    """
    Channel link added - Sent when two channels are linked together.
    """

    from_channel = None
    to_channel = None

    def __init__(self, caller, from_, to_):
        self.from_channel = from_
        self.to_channel = to_

        super(self.__class__, self).__init__(caller)


class ChannelUnlinked(MumbleEvent):
    """
    Channel link removed - Sent when two channels have their link removed.
    """

    from_channel = None
    to_channel = None

    def __init__(self, caller, from_, to_):
        self.from_channel = from_
        self.to_channel = to_

        super(self.__class__, self).__init__(caller)


# Channel state             []
# User state                []
# Text message              (Actor, session, channel, tree ID, message)