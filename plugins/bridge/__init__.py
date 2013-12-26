# coding=utf-8
__author__ = 'Gareth Coles'

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.plugin import PluginObject

from utils.config import YamlConfig


class BridgePlugin(PluginObject):

    config = None
    events = None
    commands = None

    def setup(self):
        self.logger.debug("Entered setup method.")
        try:
            self.config = YamlConfig("plugins/bridge.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling..")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/bridge.yml")
            self.logger.error("Disabling..")
            self._disable_self()
            return

        self.commands = CommandManager.instance()
        self.events = EventManager.instance()
