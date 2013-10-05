__author__ = 'Gareth Coles'

from system.events.base import BaseEvent


class MumbleEvent(BaseEvent):
    """
    A Mumble event. This will only be thrown from the Mumble protocol.
    If an event subclasses this, chances are it's a Mumble event.
    """

    def __init__(self, caller):
        super(MumbleEvent, self).__init__(caller)
