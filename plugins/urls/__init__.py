__author__ = 'Gareth Coles'

# Managers
from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.storage.manager import StorageManager

# Storage formats
from system.storage.formats import Formats

# Plugin
from system.plugins.plugin import PluginObject

# Internals
from plugins.urls.handlers.website import WebsiteHandler


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

        self.add_handler(WebsiteHandler(self))

    def reload(self):
        pass

    def deactivate(self):
        self.handlers = []

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
