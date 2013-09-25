# coding=utf-8
__author__ = "Gareth Coles"

import logging

from utils.log import getLogger

from utils.config import Config
from utils.misc import output_exception
from system.factory import Factory
from twisted.internet import reactor


class Manager(object):
    """
    Manager for keeping track of multiple factories - one per protocol.

    This is so that the bot can connect to multiple services at once, and have them communicate with each other.

    It is currently not planned to have multiple instances of a single factory.
    """

    factories = {}
    configs = {}

    main_config = None

    def __init__(self):
        self.logger = getLogger("Manager")
        self.logger.info("Loading configuration..")

        try:
            self.logger.info("Loading global configuration..")
            self.main_config = Config("config/settings.yml")
            if not self.main_config.exists:
                self.logger.error("Main configuration not found! Please correct this and try again.")
                return
        except IOError:
            self.logger.error("Unable to load main configuration at config/settings.yml")
            self.logger.error("Please check that this file exists.")
            exit(1)
        except Exception:
            self.logger.error("Unable to load main configuration at config/settings.yml")
            output_exception(self.logger, logging.ERROR)
            exit(1)

        for protocol in self.main_config["protocols"]:
            try:
                self.logger.info("Loading configuration for the '%s' protocol.." % protocol)
                conf_location = "config/protocols/%s.yml" % protocol
                config = Config(conf_location)
                if not config.exists:
                    self.logger.error("Configuration at '%s' not found!" % conf_location)
                    continue
            except IOError:
                self.logger.error("Unable to load configuration for the '%s' protocol." % protocol)
                self.logger.error("Please check that this file exists.")
                continue
            except Exception:
                self.logger.error("Unable to load configuration for the '%s' protocol." % protocol)
                output_exception(self.logger, logging.ERROR)
                continue

            try:
                self.factories[protocol] = Factory(protocol, config, self)
            except Exception:
                self.logger.error("Unable to create factory for the '%s' protocol!" % protocol)
                output_exception(self.logger, logging.ERROR)

        reactor.run()
