__author__ = 'Gareth Coles'

from system.events.base import PluginEvent


class URLCaughtEvent(PluginEvent):
    protocol = None
    user = None
    source = None

    url = {
        "protocol": None,
        "basic": None,
        "domain": None,
        "port": None,
        "path": None
    }

    def __init__(self, caller):
        super(URLCaughtEvent, self).__init__(caller)
