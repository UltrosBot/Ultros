# coding=utf-8
__author__ = 'Gareth Coles'

from collections import defaultdict
from kitchen.text.converters import to_unicode
from twisted.internet.defer import Deferred, inlineCallbacks

# Managers
from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.storage.manager import StorageManager

# Storage formats
from system.storage.formats import Formats

# Plugin
from system.plugins.plugin import PluginObject

# Internals
from plugins.urls.constants import PREFIX_TRANSLATIONS
from plugins.urls.handlers.website import WebsiteHandler
from plugins.urls.matching import extract_urls, regex_type
from plugins.urls.url import URL


class URLsPlugin(PluginObject):
    # Managers
    commands = None
    events = None
    storage = None

    config = None

    handlers = defaultdict(list)

    def setup(self):
        # TODO: Loading event
        # TODO: Channel config/commands
        # TODO: Shorteners
        self.commands = CommandManager()
        self.events = EventManager()
        self.storage = StorageManager()

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

        self.config.add_callback(self.reload)
        self.reload()

        def message_event_filter(event):
            return event.type == "message"

        self.events.add_callback("MessageReceived", self, self.message_handler,
                                 1, message_event_filter)

        self.add_handler(WebsiteHandler(self), -100)

    def reload(self):
        pass

    def deactivate(self):
        for handler_list in self.handlers.itervalues():
            for handler in handler_list:
                try:
                    handler.teardown()
                except Exception as e:
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

            yield self.run_handlers(_url, {
                "event": event,
                "config": self.config
            })

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

    def translate_prefix(self, prefix):
        # We translate some characters that are likely to be matched with
        # different ones at the end of the path here, which is about the
        # most we can do to fix this.

        prefix = to_unicode(prefix)

        for key, value in PREFIX_TRANSLATIONS.iteritems():
            prefix = prefix.replace(key, value)

        return prefix
