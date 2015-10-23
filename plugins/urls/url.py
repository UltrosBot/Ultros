import idna
from kitchen.text.converters import to_unicode, to_bytes

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
        return to_bytes(
            u"<{u.__class__.__name__} at {addr} | "
            u"{u.protocol} :// "
            u"{u.auth} @ "
            u"{u.domain} : "
            u"{u.port} / {u.path} ? "
            u"{u.query} # {u.fragment}"
            u">".format(addr=id(self), u=self)
        )

    def to_string(self, *omit):
        _format = [u""]

        if "protocol" not in omit:
            _format.append(u"{url.protocol}://")

        if "auth" not in omit:
            if self.auth:
                _format.append(u"{url.auth}@")

        if "domain" not in omit:
            _format.append(u"{url.domain}")

        if "port" not in omit:
            if self.port:
                _format.append(u":{url.port}")

        if "path" not in omit:
            _format.append(u"{url.path}")

        if "query" not in omit:
            if self.query:
                query_parts = []

                _format.append(u"?")
                for k, v in self.query.iteritems():
                    if v:
                        query_parts.append(u"{}={}".format(k, v))
                    else:
                        query_parts.append(k)

                _format.append(u"&".join(query_parts))

        if "fragment" not in omit:
            if self.fragment:
                _format.append(u"#{url.fragment}")

        return u"".join(_format).format(url=self)

    def __unicode__(self):
        return self.to_string()

    def __str__(self):
        return to_bytes(self.to_string())
