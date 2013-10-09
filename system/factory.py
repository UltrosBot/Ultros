# coding=utf-8
__author__ = "Gareth Coles"

import importlib
import logging

from twisted.internet import protocol, reactor  # , reactor, ssl

from utils.misc import output_exception
from utils.log import getLogger


class Factory(protocol.ClientFactory):
    protocol = None
    reconnecting = False
    attempts = 0

    def __init__(self, protocol_name, config, manager):
        self.logger = getLogger("*" + protocol_name)
        self.config = config
        self.manager = manager
        manager_config = manager.main_config
        reconnections = manager_config["reconnections"]
        self.r_delay = int(reconnections["delay"])
        self.r_attempts = int(reconnections["attempts"])
        self.r_on_drop = reconnections["on-drop"]
        self.r_on_failure = reconnections["on-failure"]
        self.r_reset = reconnections["reset-on-success"]

        try:
            current_protocol = importlib.import_module(
                "system.protocols.%s.protocol" % protocol_name)
            self.protocol_class = current_protocol
        except ImportError:
            self.logger.error(
                "Unable to import protocol %s" % protocol_name)
            output_exception(self.logger, logging.ERROR)
        else:
            self.protocol = current_protocol.Protocol(self, config)

    def clientConnectionLost(self, connector, reason):
        """ Called when the client loses connection """
        self.logger.warn("Lost connection: %s" % reason.__str__())
        if self.r_on_drop:
            self.attempts += 1
            self.logger.info("Reconnecting after %s seconds (attempt %s/%s)"
                             % (self.r_delay, self.attempts, self.r_attempts))
            reactor.callLater(self.r_delay, connector.connect)


    def clientConnectionFailed(self, connector, reason):
        """ Called when the client fails to connect """
        self.logger.warn("Connection failed: %s" % reason.__str__())
        if self.r_on_drop or self.reconnecting:
            if self.attempts >= self.r_attempts:
                self.logger.error("Unable to connect after %s attempts, "
                                  "aborting." % self.attempts)
                return
            self.attempts += 1
            self.logger.info("Reconnecting after %s seconds (attempt %s/%s)"
                             % (self.r_delay, self.attempts, self.r_attempts))
            reactor.callLater(self.r_delay, connector.connect)

