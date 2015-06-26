__author__ = 'Gareth Coles'

import idna
import re
import socket

from bs4 import BeautifulSoup
from kitchen.text.converters import to_unicode, to_bytes
from netaddr import IPAddress
from twisted.web._newclient import ResponseNeverReceived
from txrequests import Session

from plugins.urls.handlers.handler import URLHandler
from utils.misc import str_to_regex_flags


class WebsiteHandler(URLHandler):
    name = "website"

    criteria = {
        "protocol": re.compile(r"http|https", str_to_regex_flags("iu"))
    }

    content_types = ["text/html", "text/webviewhtml", "message/rfc822",
                     "text/x-server-parsed-html", "application/xhtml+xml"]

    def call(self, url, context):
        # TODO: Blacklist
        # TODO: Channel settings
        # TODO: Custom spoofing
        # TODO: Accept-Language
        # TODO: Cookies

        try:
            domain = idna.encode(to_unicode(url.domain), uts46=True)

            self.urls_plugin.logger.debug(
                "Domain: {0} -> {1}", domain, url.domain
            )

            ip = IPAddress(socket.gethostbyname(domain))
        except Exception as e:
            context["event"].target.respond(
                '"{0}" at {1}'.format(e, url.domain)
            )

            self.plugin.logger.warn(str(e))
            return False

        if ip.is_loopback() or ip.is_private() or ip.is_link_local():
            self.plugin.logger.warn("Prevented a portscan")
            return False

        _format = "{url.protocol}://"

        if url.auth:
            _format += "{url.auth}@"

        _format += "{domain}"

        if url.port:
            _format += ":{url.port}"

        _format += "{url.path}"
        target = _format.format(url=url, domain=domain)

        headers = {"User-Agent": ("Mozilla/5.0 (X11; U; Linux i686; "
                                  "en-US; rv:1.9.0.1) Gecko/20080716"
                                  "15 Fedora/3.0.1-1.fc9-1.fc9 "
                                  "Firefox/3.0.1")}

        session = Session()
        session.get(target, headers=headers)\
            .addCallback(self.callback, url, context)\
            .addErrback(self.errback, url, context)

        # treq.get(target, headers=headers) \
        #     .addCallback(self.callback, url, context) \
        #     .addErrback(self.errback, url, context)

        return False

    def callback(self, response, url, context):
        self.plugin.logger.trace(
            "Headers: {0}", list(response.headers)
        )
        self.plugin.logger.trace("HTTP code: {0}", response.status_code)

        if response.headers["content-type"].lower() not in self.content_types:
            self.plugin.logger.debug(
                "Unsupported Content-Type: %s"
                % response.headers["content-type"]
            )
            return  # Not a supported content-type

        soup = BeautifulSoup(response.text)

        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            title = re.sub("\s+", " ", title)
            title = title

            context["event"].target.respond(
                to_unicode('"{0}" at {1}'.format(
                    to_bytes(title), to_bytes(url.domain)
                ))
            )
        else:
            self.plugin.logger.debug("No title")

    def errback(self, error, url, context):
        self.plugin.logger.error("Error parsing URL")

        if isinstance(error.value, ResponseNeverReceived):
            for f in error.value.reasons:
                f.printDetailedTraceback()
                context["event"].target.respond(
                    '"{0}" at {1}'.format(f.getErrorMessage(), url.domain)
                )
        else:
            context["event"].target.respond(
                '"{0}" at {1}'.format(error.getErrorMessage(), url.domain)
            )
            error.printDetailedTraceback()
