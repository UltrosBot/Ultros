# coding=utf-8
__author__ = "Gareth Coles"

import importlib
import logging

from twisted.internet import protocol, reactor  # , reactor, ssl

from system.protocols.generic.protocol import Protocol as GenericProtocol
from utils.misc import output_exception
from utils.log import getLogger


class Factory(protocol.ClientFactory):
    """
    A Twisted factory, for producing protocols.

    This is a bit unorthodox as Ultros' factories never need to create more
    than one instance of a protocol, for configuration reasons.

    You'll **never** need to work with this class directly. It's very
    important, if you find that you need something extra in this class
    then raise a ticket on GitHub or submit a pull request instead of
    duck-punching it.
    """

    protocol = None
    reconnecting = False
    attempts = 0

    def __init__(self, protocol_name, config, manager):
        self.logger = getLogger("*" + protocol_name)
        self.config = config
        self.manager = manager
        self.name = protocol_name
        self.ptype = config["main"]["protocol-type"]
        self.protocol_class = None
        self.protocol = None
        manager_config = manager.main_config
        reconnections = manager_config["reconnections"]
        self.r_delay = int(reconnections["delay"])
        self.r_attempts = int(reconnections["attempts"])
        self.r_on_drop = reconnections["on-drop"]
        self.r_on_failure = reconnections["on-failure"]
        self.r_reset = reconnections["reset-on-success"]

    def setup(self):
        try:
            current_protocol = importlib.import_module(
                "system.protocols.%s.protocol" % self.ptype)
            self.protocol_class = current_protocol
        except ImportError:
            self.logger.error(
                "Unable to import protocol %s for %s" %
                (self.ptype, self.name))
            output_exception(self.logger, logging.ERROR)
        else:
            if issubclass(current_protocol.Protocol, GenericProtocol):
                self.protocol = current_protocol.Protocol(self.name,
                                                          self,
                                                          self.config)
            else:
                raise TypeError("Protocol does not subclass the generic "
                                "protocol class!")

    def buildProtocol(self, addr):
        return self.protocol

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
