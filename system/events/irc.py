__author__ = 'Gareth Coles'

from system.events.base import BaseEvent


class IRCEvent(BaseEvent):
    """
    An IRC event. This will only be thrown from the IRC protocol.
    If an event subclasses this, chances are it's an IRC event.
    """

    def __init__(self, caller):
        super(IRCEvent, self).__init__(caller)

# MOTD
# Joined channel (self)
# Parted channel (self)
# CTCP query
# Kicked from channel (self)
# Joined channel (other)
# Parted channel (other)
# Kicked from channel (other)
# User disconnected
# Topic updated
# WHO reply
# End of WHO reply
# Ban list
# End of ban list
# NAMES reply
# End of NAMES reply
# Unable to join channel: invite-only
# Unable to do command
# Channel creation details
# LOCALUSERS reply
# GLOBALUSERS reply
# VHOST set
# PONG (do we need this?)
# Unhandled message (+type)
