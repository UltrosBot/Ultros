# coding=utf-8
__author__ = "Gareth Coles"

import logging
from system.plugins import g

from system.factory import Factory
from utils.log import getLogger
from utils.config import Config
from utils.misc import output_exception

from twisted.internet import reactor
from yapsy.PluginManager import PluginManagerSingleton


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
            self.main_config = Config("config/settings.yml")
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

        self.logger.info("Loading plugins..")

        self.plugman = PluginManagerSingleton.get()
        self.plugman.setPluginPlaces(["plugins/global"])
        self.plugman.setPluginInfoExtension("plug")
        self.plugman.collectPlugins()

        for info in self.plugman.getAllPlugins():
            name = info.name
            if name in self.main_config["plugins"]:
                try:
                    if isinstance(info.plugin_object, g.GlobalPlugin):
                        self.plugman.activatePluginByName(info.name)
                        info.plugin_object.add_variables(info, self)
                        info.plugin_object.setup()
                    else:
                        self.logger.error("Plugin '%s' is not a global plugin!"
                                          % name)
                        continue
                except Exception:
                    self.logger.warn("Unable to load plugin: %s v%s"
                                     % (name, info.version))
                    output_exception(self.logger, logging.WARN)
                    self.plugman.deactivatePluginByName(name)
                else:
                    self.logger.info("Loaded plugin: %s v%s"
                                     % (name, info.version))

        # Load up the protocols

        self.logger.info("Setting up protocols..")

        for protocol in self.main_config["protocols"]:
            try:
                self.logger.info(
                    "Loading configuration for the '%s' protocol.." % protocol)
                conf_location = "config/protocols/%s.yml" % protocol
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
                self.logger.info("Finished setting up protocol '%s'."
                                 % protocol)
            except Exception:
                self.logger.error(
                    "Unable to create factory for the '%s' protocol!"
                    % protocol)
                output_exception(self.logger, logging.ERROR)

        reactor.run()
