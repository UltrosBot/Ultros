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
# from plugins.urls.handlers.handler import URLHandler


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

    def reload(self):
        pass

    def deactivate(self):
        self.handlers = []

    def add_handler(self, handler):
        handler.urls_plugin = self
        self.handlers.insert(0, handler)
