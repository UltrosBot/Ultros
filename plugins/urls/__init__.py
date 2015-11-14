# coding=utf-8

import re

from copy import copy
from collections import defaultdict

from kitchen.text.converters import to_unicode
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.python.failure import Failure
from txrequests import Session
from plugins.urls.lazy import LazyRequest
from plugins.urls.priority import Priority
from plugins.urls.shorteners.exceptions import ShortenerDown
from system.protocols.generic.channel import Channel
from system.storage.formats import Formats
from system.plugins.plugin import PluginObject
from plugins.urls.constants import PREFIX_TRANSLATIONS, CASCADE, STOP_HANDLING
from plugins.urls.events import URLsPluginLoaded
from plugins.urls.handlers.website import WebsiteHandler
from plugins.urls.matching import extract_urls
from plugins.urls.shorteners.tinyurl import TinyURLShortener
from plugins.urls.url import URL
from utils.misc import str_to_regex_flags

__author__ = 'Gareth Coles'


HTTP_S_REGEX = re.compile("http|https", flags=str_to_regex_flags("iu"))


class URLsPlugin(PluginObject):
    channels = None
    config = None
    shortened = None

    shorteners = None
    handlers = None

    def setup(self):
        self.shorteners = {}
        self.handlers = defaultdict(list)

        # Load up the configuration

        try:
            self.config = self.storage.get_file(
                self, "config", Formats.YAML, "plugins/urls.yml"
            )
        except Exception:
            self.logger.exception("Error loading configuration")
            return self._disable_self()

        if not self.config.exists:
            self.logger.error("Unable to load configuration: File not found\n"
                              "Did you fill out `config/plugins/urls.yml`?")
            return self._disable_self()

        if self.config.get("version", 1) < 2:
            self.logger.warn(
                "========================================================= \n"
                " It appears that you haven't updated your configuration.  \n"
                " Please check the example configuration and update your   \n"
                " file to match.                                           \n"
                "========================================================= \n"
            )

        self.channels = self.storage.get_file(
            self, "data", Formats.YAML, "plugins/urls/channels.yml"
        )

        self.shortened = self.storage.get_file(
            self,
            "data",
            Formats.DBAPI,
            "sqlite3:data/plugins/urls/shortened.sqlite",
            "data/plugins/urls/shortened.sqlite",
            check_same_thread=False
        )

        self.config.add_callback(self.reload)
        self.reload()

        def message_event_filter(event):
            return event.type == "message"

        self.events.add_callback("MessageReceived", self, self.message_handler,
                                 1, message_event_filter)

        self.add_handler(WebsiteHandler(self), Priority.MONITOR)
        self.add_shortener(TinyURLShortener(self))

        self.commands.register_command("urls", self.urls_command, self,
                                       "urls.manage")
        self.commands.register_command("shorten", self.shorten_command, self,
                                       "urls.shorten", default=True)

        if not self.factory_manager.running:
            self.events.add_callback(
                "ReactorStarted", self, self.send_event, 0
            )
        else:
            self.send_event()

    @property
    def default_shortener(self):
        shortener = self.config.get("default_shortener", "tinyurl")

        return shortener if self.has_shortener(shortener) else "tinyurl"

    def send_event(self, _=None):
        self.events.run_callback("URLs/PluginLoaded", URLsPluginLoaded(self))

    def reload(self):
        self.shortened.runQuery("CREATE TABLE IF NOT EXISTS urls ("
                                "url TEXT, "
                                "shortener TEXT, "
                                "result TEXT)")

        for handler_list in self.handlers.itervalues():
            for handler in handler_list:
                handler.reload()

    @inlineCallbacks
    def shorten(self, _url, shortener=None, target=None):
        if isinstance(_url, basestring):
            match = extract_urls(_url)

            if len(match) < 1:
                return

            _url = self.match_to_url(match[0])

        if target is not None:
            shortener = self.get_shortener(target)

        if shortener is None:
            shortener = self.default_shortener

        context = {"url": _url}

        r = yield self.shortened.runQuery(
            "SELECT result FROM urls WHERE url=? AND shortener=?",
            (unicode(_url), shortener.lower())
        )

        if len(r):
            returnValue(r[0][0])
        else:
            if shortener in self.shorteners:
                try:
                    result = yield self.shorteners[shortener].do_shorten(
                        context
                    )
                except ShortenerDown as e:
                    returnValue(
                        "Shortener \"{}\" appears to be down -"
                        " try again later. ({})".format(shortener, e.message)
                    )
                except Exception:
                    raise
                else:
                    self.shortened.runQuery(
                        "INSERT INTO urls VALUES (?, ?, ?)",
                        (unicode(_url), shortener.lower(), result)
                    )

                    returnValue(result)

    def get_shortener(self, target):
        shortener = (
            self.channels.get(target.protocol.name, {})
                .get(target.name, {})
                .get("shortener", self.default_shortener)
        )

        if self.has_shortener(shortener):
            return shortener

        return self.default_shortener

    def deactivate(self):
        for handler_list in self.handlers.itervalues():
            for handler in handler_list:
                try:
                    handler.teardown()
                except Exception:
                    self.logger.exception(
                        "Error tearing down handler {0}".format(handler.name)
                    )

        self.handlers = defaultdict(list)

    @inlineCallbacks
    def message_handler(self, event):
        """
        Event handler for general messages
        """

        protocol = event.caller
        source = event.source
        target = event.target
        message = event.message

        allowed = self.commands.perm_handler.check("urls.trigger", source,
                                                   target, protocol)

        if not allowed:
            return

        status = self.channels.get(protocol.name, {})\
            .get(target.name, {})\
            .get("status", True)

        if not status or status == "off":
            return

        matches = extract_urls(message)

        for match in matches:
            self.logger.trace("match: {0}", match)

            _url = self.match_to_url(match)

            if _url is None:
                continue

            # Check redirects, following as necessary

            redirects = 0
            max_redirects = self.config.get("redirects", {}).get("max", 15)
            domains = self.config.get("redirects", {}).get("domains", [])

            self.logger.debug("Checking redirects...")

            while _url.domain in domains and redirects < max_redirects:
                redirects += 1

                session = Session()

                #: :type: requests.Response
                r = yield session.get(unicode(_url), allow_redirects=False)

                if r.is_redirect:
                    # This only ever happens when we have a well-formed
                    # redirect that could have been handled automatically

                    redirect_url = r.headers["location"]

                    self.logger.debug(
                        "Redirect [{0:03d}] {1}".format(
                            redirects, redirect_url
                        )
                    )

                    _url = self.match_to_url(extract_urls(redirect_url)[0])
                else:
                    break

            if redirects >= max_redirects:
                self.logger.debug("URL has exceeded the redirects limit")
                return

            lazy_request = LazyRequest(req_args=[unicode(_url)])

            self.channels.get(protocol.name, {}) \
                .get(source.name, {})["last"] = unicode(_url)

            yield self.run_handlers(_url, {
                "event": event,
                "config": self.config,
                "get_request": lazy_request,
                "redirects": redirects,
                "max_redirects": max_redirects
            })

    def match_to_url(self, match):
        """
        :rtype: URL
        """
        # Expand the match to make it easier to work with

        # Input: ''http://x:y@tools.ietf.org:80/html/rfc1149''
        # Match: '', http, x:y, tools.ietf.org, :80, /html/rfc1149''

        _prefix, _protocol, _basic, _domain, _port, _path = (
            to_unicode(x) for x in match
        )

        _port = _port.lstrip(":")  # Remove this as the regex captures it

        try:
            if _port:
                _port = int(_port)
        except ValueError:
            self.logger.warn("Invalid port: {0}", _port)
            return None

        _translated = self.translate_prefix(_prefix)

        if len(_path) > 0 and len(_translated) > 0:
            # Remove translated prefix chars.
            for char in reversed(_translated):
                if _path[-1] == char:
                    _path = _path[:-1]
        elif len(_domain) > 0 and len(_translated) > 0:
            # Remove translated prefix chars.
            for char in reversed(_translated):
                if _domain[-1] == char:
                    _domain = _domain[:-1]

        _query = None
        _fragment = None

        if HTTP_S_REGEX.match(_protocol):
            # Parse out query/fragment from the http/s URL

            if "#" in _path:
                _path, _fragment = _path.split("#", 1)
            if "?" in _path:
                _path, _query_string = _path.split("?", 1)
                _query = {}

                for element in _query_string.split("&"):
                    if "=" in element:
                        left, right = element.split("=", 1)
                        _query[left] = right
                    else:
                        _query[element] = None

        return URL(
            self, _protocol, _basic, _domain, _port, _path, _query, _fragment
        )

    def urls_command(self, protocol, caller, source, command, raw_args,
                     parsed_args):
        """
        Command handler for the urls command
        """

        if not isinstance(source, Channel):
            caller.respond("This command can only be used in a channel.")
            return
        if len(parsed_args) < 2:
            caller.respond("Usage: {CHARS}%s <setting> <value>" % command)
            caller.respond("Operations: set <on/off> - Enable or disable "
                           "title parsing for the current channel")
            caller.respond("  shortener <name> - Set which URL shortener to "
                           "use for the current channel")
            caller.respond("  Shorteners: {0}".format(", ".join(
                self.shorteners.keys()
            )))
            return

        operation = parsed_args[0].lower()
        value = parsed_args[1].lower()

        if protocol.name not in self.channels:
            with self.channels:
                self.channels[protocol.name] = {
                    source.name: {
                        "status": True,
                        "last": "",
                        "shortener": self.default_shortener
                    }
                }
        elif source.name not in self.channels[protocol.name]:
            with self.channels:
                self.channels[protocol.name][source.name] = {
                    "status": True,
                    "last": "",
                    "shortener": self.default_shortener
                }

        if operation == "set":
            if value not in ["on", "off"]:
                caller.respond("Usage: {CHARS}urls set <on|off>")
            else:
                with self.channels:
                    self.channels[protocol.name][source.name]["status"] = (
                        value == "on"
                    )
                caller.respond("Title passing for %s turned %s."
                               % (source.name, value))
        elif operation == "shortener":
            if value.lower() in self.shorteners:
                with self.channels:
                    self.channels[protocol.name][source.name]["shortener"] \
                        = value.lower()
                caller.respond("URL shortener for %s set to %s."
                               % (source.name, value))
            else:
                caller.respond("Unknown shortener: %s." % value)
        else:
            caller.respond("Unknown operation: '%s'." % operation)

    def _respond_shorten(self, result, source, handler):
        """
        Respond to a shorten command, after a successful Deferred
        """

        if result is not None:
            return source.respond(result)

        source.respond("Unable to shorten using handler %s. Poke the bot "
                       "owner!" % handler)

    def _respond_shorten_fail(self, failure, source, handler):
        """
        Respond to a shorten command, after a failed Deferred
        """

        self.logger.error("Error shortening url with handler '{}': {}".format(
            handler, failure.value
        ))
        source.respond("Error shortening url; please notify the bot owner")

    def shorten_command(self, protocol, caller, source, command, raw_args,
                        parsed_args):
        """
        Command handler for the shorten command
        """

        if not isinstance(source, Channel):
            if len(parsed_args) == 0:
                caller.respond("Usage: {CHARS}shorten [url]")
                return
            else:
                handler = self.default_shortener
                _url = parsed_args[0]
                try:
                    d = self.shorten(_url, handler)
                    d.addCallbacks(self._respond_shorten,
                                   self._respond_shorten_fail,
                                   callbackArgs=(source, handler),
                                   errbackArgs=(source, handler))
                except Exception:
                    self.logger.exception("Error fetching short URL.")
                    caller.respond("Error fetching short URL.")
        else:
            if protocol.name not in self.channels \
                    or source.name not in self.channels[protocol.name] \
                    or not len(
                        self.channels[protocol.name][source.name]["last"]):
                caller.respond("Nobody's linked anything here yet")
                return

            handler = self.get_shortener(source)

            if not self.has_shortener(handler):  # Shouldn't happen
                caller.respond("Shortener '%s' not found - please set a "
                               "new one!" % handler)
                return

            _url = self.channels[protocol.name][source.name]["last"]

            if len(parsed_args) > 0:
                _url = parsed_args[0]

            try:
                d = self.shorten(_url, handler)
                d.addCallbacks(self._respond_shorten,
                               self._respond_shorten_fail,
                               callbackArgs=(source, handler),
                               errbackArgs=(source, handler))
            except Exception as e:
                self.logger.exception("Error fetching short URL.")
                caller.respond("Error fetching short URL.")

    def check_blacklist(self, _url, context):
        for entry in context["config"]["blacklist"]:
            if re.match(entry, _url, flags=str_to_regex_flags("ui")):
                self.logger.debug(
                    "Matched blacklist regex: %s" % entry
                )
                return True

        return False

    @inlineCallbacks
    def run_handlers(self, _url, context):
        if self.check_blacklist(_url, context):
            self.logger.debug(
                "URL {0} is blacklisted; ignoring...".format(_url)
            )
            return

        for priority in reversed(sorted(self.handlers.iterkeys())):
            for handler in self.handlers[priority]:
                try:
                    d = handler.match(_url, context)
                except Exception:
                    self.logger.exception(
                        "Error caught while attempting to match "
                        "handler {0}".format(
                            handler.name
                        )
                    )

                    continue

                if isinstance(d, Deferred):
                    r = yield d
                else:
                    r = d

                if isinstance(r, Failure):
                    self.logger.error(
                        "Error caught while attempting to match "
                        "handler {0}".format(
                            handler.name
                        )
                    )

                    r.printTraceback()
                    continue

                if r:
                    try:
                        d = handler.call(_url, context)
                    except Exception:
                        self.logger.exception(
                            "Error caught while attempting to call "
                            "handler {0}".format(
                                handler.name
                            )
                        )

                        continue

                    if isinstance(d, Deferred):
                        r = yield d
                    else:
                        r = d
                    if isinstance(r, Failure):
                        self.logger.error(
                            "Error caught while attempting to call "
                            "handler {0}".format(
                                handler.name
                            )
                        )

                        r.printTraceback()
                        continue
                    elif r == STOP_HANDLING:
                        return

    def add_handler(self, handler, priority=0):
        if not self.has_handler(handler.name):  # Only add if it's not there
            self.logger.debug("Adding handler: {}".format(handler.name))
            handler.urls_plugin = self

            self.handlers[priority].append(handler)
        else:
            self.logger.warn("Handler {} is already registered!".format(
                handler.name
            ))

    def has_handler(self, name):
        for priority in self.handlers.iterkeys():
            for handler in self.handlers[priority]:
                if name == handler.name:
                    return True

        return False

    def remove_handler(self, handler):
        for handler_list in self.handlers.itervalues():
            for _handler in copy(handler_list):
                if handler == _handler.name:
                    handler_list.remove(_handler)

    def add_shortener(self, shortener):
        if not self.has_handler(shortener.name):
            shortener.urls_plugin = self
            self.shorteners[shortener.name] = shortener

    def has_shortener(self, shortener):
        return shortener in self.shorteners

    def remove_shortener(self, shortener):
        if self.has_shortener(shortener):
            del self.shorteners[shortener]

    def translate_prefix(self, prefix):
        # We translate some characters that are likely to be matched with
        # different ones at the end of the path here, which is about the
        # most we can do to fix this.

        prefix = to_unicode(prefix)

        for key, value in PREFIX_TRANSLATIONS.iteritems():
            prefix = prefix.replace(key, value)

        return prefix
