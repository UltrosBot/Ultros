__author__ = 'Gareth Coles'


class URL(object):
    plugin = None

    protocol = None
    auth = None
    domain = None
    port = None
    path = None

    def __init__(self, plugin=None, protocol=None, auth=None, domain=None,
                 port=None, path=None):
        self.plugin = plugin

        self.protocol = protocol
        self.auth = auth
        self.domain = domain
        self.port = port
        self.path = path

    def shorten(self, shortener=None, shorten_for=None):
        pass
