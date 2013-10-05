__author__ = 'Gareth Coles'

from system.events.base import BaseEvent


class GeneralEvent(BaseEvent):
    """
    A general event, not tied to a protocol.
    If an event subclasses this, chances are it's a protocol-agnostic event.
    """

    def __init__(self, caller):
        super(GeneralEvent, self).__init__(caller)
