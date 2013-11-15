# coding=utf-8
__author__ = "Gareth Coles"

import logging

from system.factory import Factory
from utils.log import getLogger
from utils.config import Config
from utils.misc import output_exception

from twisted.internet import reactor
from system.plugin_manager import YamlPluginManagerSingleton

from system.command_manager import CommandManager


class Manager(object):
    """
    Manager for keeping track of multiple factories - one per protocol.

    This is so that the bot can connect to multiple services at once, and have
    them communicate with each other.

    It is currently not planned to have multiple instances of a single factory.
    """

    factories = {}
    configs = {}

    main_config = None

    def __init__(self):
        # Set up the logger
        self.logger = getLogger("Manager")

        # Load up the main configuration
        self.logger.info("Loading configuration..")

        try:
            self.logger.info("Loading global configuration..")
            self.main_config = Config("settings.yml")
            if not self.main_config.exists:
                self.logger.error(
                    "Main configuration not found! Please correct this and try"
                    " again.")
                return
        except IOError:
            self.logger.error(
                "Unable to load main configuration at config/settings.yml")
            self.logger.error("Please check that this file exists.")
            exit(1)
        except Exception:
            self.logger.error(
                "Unable to load main configuration at config/settings.yml")
            output_exception(self.logger, logging.ERROR)
            exit(1)

        # Load up the plugins

        self.commands = CommandManager.instance()
        self.commands.set_factory_manager(self)

        self.logger.info("Loading plugins..")

        self.logger.debug("Configured plugins: %s"
                          % ", ".join(self.main_config["plugins"]))

        self.plugman = YamlPluginManagerSingleton.instance()
        self.plugman.setPluginPlaces(["plugins"])
        self.plugman.setPluginInfoExtension("plug")

        self.logger.debug("Collecting plugins..")
        self.plugman.collectPlugins()

        for info in self.plugman.getAllPlugins():
            name = info.name
            self.logger.debug("Checking if plugin '%s' is configured to load.."
                              % name)
            if name in self.main_config["plugins"]:
                try:
                    self.plugman.activatePluginByName(info.name)
                    info.plugin_object.add_variables(info, self)
                    if hasattr(info.plugin_object, "setup"):
                        self.logger.debug("Running setup method..")
                        info.plugin_object.setup()
                except Exception:
                    self.logger.warn("Unable to load plugin: %s v%s"
                                     % (name, info.version))
                    output_exception(self.logger, logging.WARN)
                    self.plugman.deactivatePluginByName(name)
                else:
                    self.logger.info("Loaded plugin: %s v%s"
                                     % (name, info.version))
                    if info.copyright:
                        self.logger.info("Licensing: %s" % info.copyright)

        # Load up the protocols

        self.logger.info("Setting up protocols..")

        for protocol in self.main_config["protocols"]:
            try:
                self.logger.info(
                    "Loading configuration for the '%s' protocol.." % protocol)
                conf_location = "protocols/%s.yml" % protocol
                config = Config(conf_location)
                if not config.exists:
                    self.logger.error(
                        "Configuration at '%s' not found!" % conf_location)
                    continue
            except IOError:
                self.logger.error(
                    "Unable to load configuration for the '%s' protocol."
                    % protocol)
                self.logger.error("Please check that this file exists.")
                continue
            except Exception:
                self.logger.error(
                    "Unable to load configuration for the '%s' protocol."
                    % protocol)
                output_exception(self.logger, logging.ERROR)
                continue

            try:
                self.factories[protocol] = Factory(protocol, config, self)
                self.factories[protocol].setup()
                self.logger.info("Finished setting up protocol '%s'."
                                 % protocol)
            except Exception:
                self.logger.error(
                    "Unable to create factory for the '%s' protocol!"
                    % protocol)
                output_exception(self.logger, logging.ERROR)

        if not len(self.factories):
            self.logger.info("It seems like no protocols are active. Shutting "
                             "down..")
            return

        reactor.run()

    def remove_protocol(self, protocol):
        if protocol in self.factories:
            del self.factories[protocol]
            return True
        return False
