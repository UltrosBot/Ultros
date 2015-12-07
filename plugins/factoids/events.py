# coding=utf-8

"""Factoid-related events"""

__author__ = 'Gareth Coles'

from system.events.base import PluginEvent


class FactoidAddedEvent(PluginEvent):
    """Event thrown when a factoid is added. This does not include when a factoid
    already exists but has a line added to it.
    """

    name = ""
    content = ""

    def __init__(self, caller, name, content):
        self.name = name
        self.content = content

        super(FactoidAddedEvent, self).__init__(caller)


class FactoidDeletedEvent(PluginEvent):
    """Event thrown when an existing factoid is deleted."""

    name = ""

    def __init__(self, caller, name):
        self.name = name

        super(FactoidDeletedEvent, self).__init__(caller)


class FactoidUpdatedEvent(PluginEvent):
    """Event thrown when an existing factoid is updated. This does include
    when a factoid already exists and has a line added to it.
    """

    name = ""
    content = ""

    def __init__(self, caller, name, content):
        self.name = name
        self.content = content

        super(FactoidUpdatedEvent, self).__init__(caller)
