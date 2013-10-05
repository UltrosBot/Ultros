__author__ = 'Gareth Coles'

from system.events.base import BaseEvent


class IRCEvent(BaseEvent):
    """
    An IRC event. This will only be thrown from the IRC protocol.
    If an event subclasses this, chances are it's a protocol-agnostic event.
    """

    def __init__(self, caller):
        super(IRCEvent, self).__init__(caller)
