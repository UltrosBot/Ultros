# coding=utf-8
__author__ = "Gareth Coles"

from utils.log import getLogger

from utils.config import Config
from utils.misc import output_exception
from system.factory import Factory


class Manager(object):
    """
    Manager for keeping track of multiple factories - one per protocol.

    This is so that the bot can connect to multiple services at once, and have them communicate with each other.
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
                self.logger.info("Loading configurationfor the '%s' protocol.." % protocol)
                config = Config("config/protocols/%s.yml" % protocol)
            except IOError:
                self.logger.error("Unable to configuration for the '%s' protocol." % protocol)
                self.logger.error("Please check that this file exists.")
                continue
            except Exception:
                self.logger.error("Unable to configuration for the '%s' protocol." % protocol)
                output_exception(self.logger, logging.ERROR)
                continue

            self.factories[protocol] = Factory(protocol, config, self)
