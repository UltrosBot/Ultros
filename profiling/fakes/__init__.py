__author__ = 'Gareth Coles'

from system.events.base import BaseEvent, PluginEvent
from system.plugins.plugin import PluginObject
from system.protocols.generic.user import User
from system.protocols.generic.protocol import Protocol

from utils.misc import AttrDict


class FakeBaseEvent(BaseEvent):
    data = {}

    def __init__(self, data):
        self.data = AttrDict(data)
        super(FakeBaseEvent, self).__init__(Protocol("Fake", None, {}))


class FakePlugin(PluginObject):
    info = {}

    def __init__(self, info=None):
        if info is None:
            info = {}

        self.info = AttrDict(info)


class FakePluginEvent(PluginEvent):
    def __init__(self):
        super(FakePluginEvent, self).__init__(FakePlugin())


class FakeUser(User):
    def __init__(self):
        super(FakeUser, self).__init__(
            "Fake User",
            Protocol("Fake", None, {})
        )

    def respond(self, message):
        print "Fake message to %s: %s" % (self.name, message)
