# coding=utf-8
__author__ = 'Gareth Coles'

from kitchen.text.converters import to_unicode

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
from plugins.urls.matching import extract_urls
from plugins.urls.url import URL

# Protocol objects
from system.protocols.generic.channel import Channel
from system.protocols.generic.user import User


class URLsPlugin(PluginObject):
    # Managers
    commands = None
    events = None
    storage = None

    config = None

    handlers = []

    def setup(self):
        self.commands = CommandManager()
        self.events = EventManager()
        self.storage = StorageManager()

        # Load up the configuration

        try:
            self.config = self.storage.get_file(
                self, "config", Formats.YAML, "plugins/urls.yml"
            )
        except Exception as e:
            self.logger.error("Error loading configuration: {}".format(e))
            return self._disable_self()

        if not self.config.exists:
            self.logger.error("Unable to load configuration: File not found")
            self.logger.error("Did you fill out `config/plugins/urls.yml`?")
            return self._disable_self()

        self.config.add_callback(self.reload)
        self.reload()

        def message_event_filter(event):
            target = event.target
            type_ = event.type

            return type_ == "message" \
                or isinstance(target, Channel) \
                or isinstance(target, User)

        self.events.add_callback("MessageReceived", self, self.message_handler,
                                 1, message_event_filter)

        self.add_handler(WebsiteHandler(self))

    def reload(self):
        pass

    def deactivate(self):
        self.handlers = []

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
            # Expand the match to make it easier to work with

            # Input: ''http://x:y@tools.ietf.org:80/html/rfc1149''
            # Match: '', http, x:y, tools.ietf.org, :80, /html/rfc1149''
            _prefix, _protocol, _basic, _domain, _port, _path = match

            _port = _port.lstrip(":")  # Remove this as the regex captures it

            try:
                _port = int(_port)
            except ValueError:
                self.logger.warn("Invalid port: {}".format(_port))
                continue

            _translated = self.translate_prefix(_prefix)

            if len(_path) and len(_translated):
                # Remove translated prefix chars.
                for char in reversed(_translated):
                    if _path[-1] == char:
                        _path = _path[:-1]

            _url = URL(self, _protocol, _basic, _domain, _port, _path)

            return _url  # TODO: Finish this function

    def add_handler(self, handler, position=None, which=None):
        if not self.has_handler(handler.name):  # Only add if it's not there
            handler.urls_plugin = self

            if which is not None and position is not None:
                # Needs to be before or after a specific handler
                if position == "before":
                    index = 0  # Start at the start

                    for h in self.handlers:
                        if which == h.name:
                            self.handlers.insert(index, handler)
                            return

                        index += 1
                elif position == "after":
                    index = len(self.handlers)  # Start at the end

                    for h in self.handlers[::-1]:
                        if which == h.name:
                            self.handlers.insert(index, handler)
                            return

                        index -= 1

            # If we can't find the specified handler to be relative to, or
            # the handler doesn't care where it is, then put it at the start.
            self.handlers.insert(0, handler)

    def has_handler(self, name):
        for handler in self.handlers:
            if name == handler.name:
                return True

        return False

    def translate_prefix(self, prefix):
        # We translate some characters that are likely to be matched with
        # different ones at the end of the path here, which is about the
        # most we can do to fix this.
        # TODO: More translations for the prefix?

        prefix = to_unicode(prefix)

        for key, value in PREFIX_TRANSLATIONS.iteritems():
            prefix = prefix.replace(key, value)

        return prefix
