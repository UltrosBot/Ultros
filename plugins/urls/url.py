import idna
from kitchen.text.converters import to_unicode

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
        self.domain = idna.encode(to_unicode(domain))
        self.port = port
        self.path = path

    def shorten(self, shortener=None, shorten_for=None):
        pass

    def __repr__(self):
        return "<{u.__class__.__name__} at {addr} | " \
               "{u.protocol} :// " \
               "{u.auth} @ " \
               "{u.domain} : " \
               "{u.port} / {u.path}" \
               ">".format(addr=id(self), u=self)

    def __str__(self):
        _format = "{url.protocol}://"

        if self.auth:
            _format += "{url.auth}@"

        _format += "{url.domain}"

        if self.port:
            _format += ":{url.port}"

        _format += "{url.path}"

        return _format.format(url=self)
