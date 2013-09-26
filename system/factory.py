# coding=utf-8
__author__ = "Gareth Coles"

import importlib

from twisted.internet import protocol  # , reactor, ssl

# from utils.misc import output_exception
from utils.log import getLogger


class Factory(protocol.ClientFactory):
    protocol = None

    def __init__(self, protocol_name, config, manager):
        self.logger = getLogger("F: " + protocol_name)
        self.config = config
        self.manager = manager

        try:
            current_protocol = importlib.import_module("system.protocols.%s.protocol" % protocol_name)
        except ImportError:
            self.logger.error("Unable to import protocol %s, does it exist?" % protocol_name)
        else:
            self.protocol = current_protocol.Protocol(self, config)

    def clientConnectionLost(self, connector, reason):
        """ Called when the client loses connection """

        pass

    def clientConnectionFailed(self, connector, reason):
        """ Called when the client fails to connect """

        pass
