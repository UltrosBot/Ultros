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
    query = None
    fragment = None

    def __init__(self, plugin=None, protocol=None, auth=None, domain=None,
                 port=None, path=None, query=None, fragment=None):
        self.plugin = plugin

        self.protocol = protocol
        self.auth = auth
        self.domain = idna.encode(to_unicode(domain))
        self.port = port
        self.path = path
        self.query = query
        self.fragment = fragment

    def shorten(self, shortener=None, shorten_for=None):
        pass

    def __repr__(self):
        return "<{u.__class__.__name__} at {addr} | " \
               "{u.protocol} :// " \
               "{u.auth} @ " \
               "{u.domain} : " \
               "{u.port} / {u.path} ? " \
               "{u.query} # {u.fragment}"\
               ">".format(addr=id(self), u=self)

    def to_string(self, *omit):
        return self.__str__(*omit)

    def __str__(self, *omit):
        _format = ""

        if "protocol" not in omit:
            _format += "{url.protocol}://"

        if "auth" not in omit:
            if self.auth:
                _format += "{url.auth}@"

        if "domain" not in omit:
            _format += "{url.domain}"

        if "port" not in omit:
            if self.port:
                _format += ":{url.port}"

        if "path" not in omit:
            _format += "{url.path}"

        if "query" not in omit:
            if self.query:
                _format += "?"
                for k, v in self.query.iteritems():
                    if v:
                        _format += "{}={}".format(k, v)
                    else:
                        _format += k

                    _format += "&"

                if _format.endswith("&"):
                    _format = _format[:-1]

        if "fragment" not in omit:
            if self.fragment:
                _format += "#{url.fragment}"

        return _format.format(url=self)
