# coding=utf-8
from copy import copy
from collections import defaultdict

from kitchen.text.converters import to_unicode
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue

from twisted.python.failure import Failure

from system.protocols.generic.channel import Channel
from system.storage.formats import Formats
from system.plugins.plugin import PluginObject
from plugins.urls.constants import PREFIX_TRANSLATIONS
from plugins.urls.events import URLsPluginLoaded
from plugins.urls.handlers.website import WebsiteHandler
from plugins.urls.matching import extract_urls
from plugins.urls.shorteners.tinyurl import TinyURLShortener
from plugins.urls.url import URL

__author__ = 'Gareth Coles'


class URLsPlugin(PluginObject):
    # Managers
    commands = None
    events = None
    storage = None

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
        except Exception as e:
            self.logger.error("Error loading configuration: {}", e)
            return self._disable_self()

        if not self.config.exists:
            self.logger.error("Unable to load configuration: File not found")
            self.logger.error("Did you fill out `config/plugins/urls.yml`?")
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

        self.add_handler(WebsiteHandler(self), -100)
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

            match = match[0]

            self.logger.trace("match: {0}", match)
            # Expand the match to make it easier to work with

            # Input: ''http://x:y@tools.ietf.org:80/html/rfc1149''
            # Match: '', http, x:y, tools.ietf.org, :80, /html/rfc1149''
            _prefix, _protocol, _basic, _domain, _port, _path = (
                to_unicode(x) for x in match
            )

            _port = _port.lstrip(":")

            try:
                if _port:
                    _port = int(_port)
            except ValueError:
                self.logger.warn("Invalid port: {0}", _port)
                return

            _url = URL(self, _protocol, _basic, _domain, _port, _path)

        if target is not None:
            shortener = self.get_shortener(target)

        if shortener is None:
            shortener = self.default_shortener

        context = {"url": _url}

        r = yield self.shortened.runQuery(
            "SELECT * FROM urls WHERE url=? AND shortener=?",
            (str(_url), shortener.lower())
        )

        if isinstance(r, Failure):
            returnValue(r)
        elif len(r):
            returnValue(r[0][2])
        else:
            if shortener in self.shorteners:
                result = yield self.shorteners[shortener].do_shorten(context)

                if isinstance(result, Failure):
                    returnValue(result)
                else:
                    self.shortened.runQuery(
                        "INSERT INTO urls VALUES (?, ?, ?)",
                        (str(_url), shortener.lower(), result)
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

        allowed = self.commands.perm_handler.check("urls.title", source,
                                                   target, protocol)

        if not allowed:
            return

        if self.channels.get(protocol.name,
                             {}).get(target.name,
                                     {}).get("status", "on") == "off":
            return

        matches = extract_urls(message)

        for match in matches:
            self.logger.trace("match: {0}", match)
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
                continue

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

            _url = URL(self, _protocol, _basic, _domain, _port, _path)

            self.channels.get(protocol.name, {}) \
                .get(source.name, {})["last"] = str(_url)

            yield self.run_handlers(_url, {
                "event": event,
                "config": self.config
            })

    def urls_command(self, protocol, caller, source, command, raw_args,
                     args):
        """
        Command handler for the urls command
        """

        if not isinstance(source, Channel):
            caller.respond("This command can only be used in a channel.")
            return
        if len(args) < 2:
            caller.respond("Usage: {CHARS}%s <setting> <value>" % command)
            caller.respond("Operations: set <on/off> - Enable or disable "
                           "title parsing for the current channel")
            caller.respond("            %s" % "shortener <name> - Set "
                                              "which URL shortener to use "
                                              "for the current channel")
            caller.respond("            %s" % "Shorteners: %s" % ", ".join(
                self.shorteners.keys()
            ))
            return

        operation = args[0].lower()
        value = args[1].lower()

        if protocol.name not in self.channels:
            with self.channels:
                self.channels[protocol.name] = {
                    source.name: {
                        "status": "on",
                        "last": "",
                        "shortener": self.default_shortener
                    }
                }
        if source.name not in self.channels[protocol.name]:
            with self.channels:
                self.channels[protocol.name][source.name] = {
                    "status": "on",
                    "last": "",
                    "shortener": self.default_shortener
                }

        if operation == "set":
            if value not in ["on", "off"]:
                caller.respond("Usage: {CHARS}urls set <on|off>")
            else:
                with self.channels:
                    self.channels[protocol.name][source.name]["status"] = value
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
                caller.respond("Unknown shortener: %s" % value)
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

        source.respond("Error shortening url with handler %s: %s" % (
            handler, failure
        ))

    def shorten_command(self, protocol, caller, source, command, raw_args,
                        args):
        """
        Command handler for the shorten command
        """

        if not isinstance(source, Channel):
            if len(args) == 0:
                caller.respond("Usage: {CHARS}shorten [url]")
                return
            else:
                handler = self.default_shortener
                _url = args[0]
                try:
                    d = self.shorten(_url, handler)
                    d.addCallbacks(self._respond_shorten,
                                   self._respond_shorten_fail,
                                   callbackArgs=(source, handler),
                                   errbackArgs=(source, handler))
                except Exception as e:
                    self.logger.exception("Error fetching short URL.")
                    caller.respond("Error: %s" % e)
        else:
            if protocol.name not in self.channels \
                    or source.name not in self.channels[protocol.name] \
                    or not len(
                        self.channels[protocol.name][source.name]["last"]):
                caller.respond("Nobody's pasted a URL here yet!")
                return

            handler = self.get_shortener(source)

            if not self.has_shortener(handler):  # Shouldn't happen
                caller.respond("Shortener '%s' not found - please set a "
                               "new one!" % handler)
                return

            _url = self.channels[protocol.name][source.name]["last"]

            if len(args) > 0:
                _url = args[0]

            try:
                d = self.shorten(_url, handler)
                d.addCallbacks(self._respond_shorten,
                               self._respond_shorten_fail,
                               callbackArgs=(source, handler),
                               errbackArgs=(source, handler))
            except Exception as e:
                self.logger.exception("Error fetching short URL.")
                caller.respond("Error: %s" % e)

    @inlineCallbacks
    def run_handlers(self, _url, context):
        for priority in reversed(sorted(self.handlers.iterkeys())):
            for handler in self.handlers[priority]:
                try:
                    d = handler.match(_url, context)
                except Exception as e:
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

                if r:
                    try:
                        d = handler.call(_url, context)
                    except Exception as e:
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
                    if not r:
                        return

    def add_handler(self, handler, priority=0):
        if not self.has_handler(handler.name):  # Only add if it's not there
            handler.urls_plugin = self

            self.handlers[priority].append(handler)

    def has_handler(self, name):
        for priority in self.handlers.iterkeys():
            for handler in self.handlers[priority]:
                if name == handler.name:
                    return True

        return False

    def remove_handler(self, handler):
        for handler_list in self.handlers.itervalues():
            for _handler in copy(handler_list):
                if handler.name == _handler.name:
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
