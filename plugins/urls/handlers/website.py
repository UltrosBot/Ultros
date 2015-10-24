# coding=utf-8

from contextlib import closing
import os
import re
import requests
import urlparse

from cookielib import LoadError
from bs4 import BeautifulSoup
from kitchen.text.converters import to_unicode
from netaddr import IPAddress
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web._newclient import ResponseNeverReceived
from txrequests import Session

from plugins.urls.constants import STATUS_CODES
from plugins.urls.cookiejar import ChocolateCookieJar
from plugins.urls.handlers.handler import URLHandler
from plugins.urls.resolver import AddressResolver
from utils.misc import str_to_regex_flags

__author__ = 'Gareth Coles'


class WebsiteHandler(URLHandler):
    name = "website"

    criteria = {
        "protocol": re.compile(r"http|https", str_to_regex_flags("iu"))
    }

    global_session = None
    resolver = None

    cookies_base_path = "data/plugins/urls/cookies"

    def __init__(self, plugin):
        self.group_sessions = {}

        super(WebsiteHandler, self).__init__(plugin)

        if not os.path.exists(self.cookies_base_path):
            os.makedirs(self.cookies_base_path)

        if not os.path.exists(self.cookies_base_path + "/groups"):
            os.makedirs(self.cookies_base_path + "/groups")

        self.reload()

    @inlineCallbacks
    def call(self, url, context):
        try:
            ip = yield self.resolver.get_host_by_name(url.domain)
            ip = IPAddress(ip)
        except Exception as e:
            context["event"].target.respond(
                'DNS failure: "{0}" at {1}'.format(e.message, url.domain)
            )

            self.plugin.logger.exception("Error while checking DNS")
            returnValue(False)
            return

        if ip.is_loopback() or ip.is_private() or ip.is_link_local() \
                or ip.is_multicast():
            self.plugin.logger.warn(
                "Prevented connection to private/internal address"
            )

            returnValue(False)
            return

        headers = {}

        if url.domain in context["config"]["spoofing"]:
            user_agent = context["config"]["spoofing"][url.domain]

            if user_agent:
                headers["User-Agent"] = user_agent
        else:
            headers["User-Agent"] = context["config"].get(
                "default_user_agent",
                "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 "
                "Firefox/36.0"
            )

        domain_langs = context.get("config") \
            .get("accept_language", {}) \
            .get("domains", {})

        if url.domain in domain_langs:
            headers["Accept-Language"] = domain_langs.get(url.domain)
        else:
            headers["Accept-Language"] = context.get("config") \
                .get("accept_language", {}) \
                .get("default", "en")

        session = self.get_session(url, context)
        session.get(unicode(url), headers=headers, stream=True,
                    background_callback=self.background_callback) \
            .addCallback(self.callback, url, context, session) \
            .addErrback(self.errback, url, context, session)

        returnValue(False)

    def teardown(self):
        # Save all our cookie stores
        if self.global_session is not None:
            self.global_session.cookies.save(ignore_discard=True)
            self.global_session.close()

        for session in self.group_sessions.itervalues():
            session.cookies.save(ignore_discard=True)
            session.close()

        if self.resolver is not None:
            self.resolver.close()

    def reload(self):
        self.teardown()
        self.group_sessions = {}
        self.resolver = AddressResolver()

        self.global_session = Session()
        try:
            self.global_session.cookies = self.get_cookie_jar("/global.txt")
            self.global_session.session_type = "global"
            self.global_session.cookies.set_mode(
                self.plugin.config.get("sessions", {})
                    .get("cookies", {})
                    .get("global", "discard")
            )
        except ValueError as e:
            self.urls_plugin.logger.error(
                "Failed to create global cookie jar: {0}".format(e)
            )

    def save_session(self, session):
        if session.session_type:
            session.cookies.save(ignore_discard=True)

    def background_callback(self, session, response):
        """
        Does basic processing of the response in the background, including
        reading the response's content. As such, response.content should not be
        used.
        :param session:
        :param response:
        :return: response, content
        """
        conns_conf = self.urls_plugin.config.get("connections", {})
        max_read = conns_conf.get("max_read_size", 1024 * 16)
        chunk_size = conns_conf.get("chunk_read_size", max_read)

        if "content-type" not in response.headers:
            response.headers["Content-Type"] = ""

        content_type = response.headers["content-type"].lower()

        if ";" in content_type:
            parts = content_type.split(";")
            content_type = parts[0]

        if content_type not in self.urls_plugin.config["content_types"]:
            self.plugin.logger.debug(
                "Unsupported Content-Type: %s"
                % response.headers["content-type"]
            )
            return response, None  # Not a supported content-type

        # If the response specifies a charset in the header, let requests
        # attempt to decode the contents. We can't use response.encoding as
        # it falls back to ISO-8859-1 in cases such as Content-Type: text/html.
        # In those cases, we want BeautifulSoup to perform its satanic ritual
        # to magically figure out the encoding.
        decode_unicode = False
        if ";" in content_type:
            for x in content_type.split(";"):
                split = x.strip().split("=")
                if len(split) > 1:
                    if split[0].lower() == "charset":
                        charset = split[1].lower()
                        if charset == "binary":
                            # Not a webpage, so return None content
                            self.urls_plugin.logger.debug(
                                "Unsupported charset: {0}", charset)
                            return response, None
                        # Contains charset header - let requests decode
                        decode_unicode = True
                        self.urls_plugin.logger.trace(
                            "Charset specified in header: {0}", charset)
                        break

        chunks_left = max_read / chunk_size
        chunks = []
        self.plugin.logger.trace("Starting read...")
        # We must close this when finished otherwise they'll hang if we don't
        # read everything
        with closing(response) as c_resp:
            for chunk in c_resp.iter_content(chunk_size=chunk_size,
                                             decode_unicode=decode_unicode):
                chunks.append(chunk)
                self.plugin.logger.trace("Read a chunk")
                chunks_left -= 1
                if chunks_left <= 0:
                    self.plugin.logger.debug(
                        "Stopped reading response after {0} bytes", max_read)
                    break
        self.plugin.logger.trace("Done reading")
        # chunks can be bytes or unicode
        if decode_unicode:
            joiner = u""
        else:
            joiner = b""
        content = joiner.join(chunks)
        self.plugin.logger.trace("background_callback done")
        return response, content

    @inlineCallbacks
    def callback(self, result, url, context, session):
        response = result[0]
        content = result[1]

        self.plugin.logger.trace(
            "Headers: {0}", list(response.headers)
        )

        self.plugin.logger.trace("HTTP code: {0}", response.status_code)

        new_url = urlparse.urlparse(response.url)

        try:
            ip = yield self.resolver.get_host_by_name(new_url.hostname)
            ip = IPAddress(ip)
        except Exception as e:
            context["event"].target.respond(
                u'DNS failure: "{0}" at {1}'.format(
                    e.message,
                    new_url.hostname
                )
            )

            self.plugin.logger.exception("Error while checking DNS")
            returnValue(False)
            return

        if ip.is_loopback() or ip.is_private() or ip.is_link_local() \
                or ip.is_multicast():
            self.plugin.logger.warn(
                "Prevented connection to private/internal address"
            )

            returnValue(False)
            return

        if content is None:
            self.plugin.logger.debug("No content returned")
            return

        soup = BeautifulSoup(content)

        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            title = re.sub("\s+", " ", title)
            title = to_unicode(title)

            if response.status_code == requests.codes.ok:
                context["event"].target.respond(
                    u'"{0}" at {1}'.format(
                        title, new_url.hostname
                    )
                )
            else:
                context["event"].target.respond(
                    u'[HTTP {0}] "{1}" at {2}'.format(
                        response.status_code,
                        title, new_url.hostname
                    )
                )

        else:
            if response.status_code != requests.codes.ok:
                context["event"].target.respond(
                    u'HTTP Error {0}: "{1}" at {2}'.format(
                        response.status_code,
                        STATUS_CODES.get(response.status_code, "Unknown"),
                        new_url.hostname
                    )
                )
            else:
                self.plugin.logger.debug("No title")

        self.save_session(session)

    @inlineCallbacks
    def errback(self, error, url, context, session):
        self.plugin.logger.error("Error parsing URL")

        if isinstance(error.value, ResponseNeverReceived):
            for f in error.value.reasons:
                f.printDetailedTraceback()
                context["event"].target.respond(
                    u'"{0}" at {1}'.format(
                        to_unicode(f.getErrorMessage()),
                        url.domain
                    )
                )
        else:
            context["event"].target.respond(
                u'"{0}" at {1}'.format(
                    to_unicode(error.getErrorMessage()),
                    url.domain
                )
            )
            error.printDetailedTraceback()

        self.save_session(session)

    def get_cookie_jar(self, filename):
        cj = ChocolateCookieJar(self.cookies_base_path + filename)

        try:
            cj.load()
        except LoadError:
            self.plugin.logger.exception(
                "Failed to load cookie jar {0}".format(filename)
            )
        except IOError as e:
            self.plugin.logger.debug(
                "Failed to load cookie jar {0}: {1}".format(filename, e)
            )

        return cj

    def get_session(self, url, context):
        sessions = context.get("config", {}).get("sessions", {})

        if not sessions.get("enable", False):
            self.urls_plugin.logger.debug("Sessions are disabled.")
            s = Session()
            s.session_type = None

            return s

        for entry in sessions["never"]:
            if re.match(entry, url.domain, flags=str_to_regex_flags("ui")):
                self.urls_plugin.logger.debug(
                    "Domain {0} is blacklisted for sessions.".format(
                        url.domain
                    )
                )
                s = Session()
                s.session_type = None

                return s

        for group, entries in sessions["group"].iteritems():
            for entry in entries:
                try:
                    if re.match(
                            entry, url.domain, flags=str_to_regex_flags("ui")
                    ):
                        self.urls_plugin.logger.debug(
                            "Domain {0} uses the '{1}' group sessions.".format(
                                url.domain, group
                            )
                        )

                        if group not in self.group_sessions:
                            self.group_sessions[group] = Session()
                            self.group_sessions[group].cookies = (
                                self.get_cookie_jar(
                                    "/groups/{0}.txt".format(
                                        group
                                    )
                                )
                            )

                            self.group_sessions[group].session_type = "group"
                            self.group_sessions[group].cookies.set_mode(
                                context.get("config")
                                .get("sessions")
                                .get("cookies")
                                .get("group")
                            )

                        return self.group_sessions[group]
                except ValueError as e:
                    self.urls_plugin.logger.error(
                        "Failed to create cookie jar: {0}".format(e)
                    )
                    continue

        self.urls_plugin.logger.debug(
            "Domain {0} uses the global session storage.".format(
                url.domain
            )
        )

        return self.global_session
