# coding=utf-8
__author__ = "Gareth Coles"

import importlib

from twisted.internet import protocol, reactor  # , reactor, ssl

from system.protocols.generic.protocol import Protocol as GenericProtocol
from utils.log import getLogger

from system.translations import Translations
_ = Translations().get()


class Factory(protocol.ClientFactory):
    """
    A Twisted factory, for producing protocols.

    This is a bit unorthodox as Ultros' factories never need to create more
    than one instance of a protocol, for configuration reasons.

    You'll **never** need to work with this class directly. It's very
    important, so if you find that you need something extra in this class
    then raise a ticket on GitHub or submit a pull request instead of
    duck-punching it.
    """

    #: The stored protocol object
    protocol = None

    #: Whether we're reconnecting or not
    reconnecting = False

    #: How many times we've tried to reconnect
    attempts = 0

    #: Whether we're currently shutting down
    shutting_down = False

    def __init__(self, protocol_name, config, manager):
        self.logger = getLogger("F: %s" % protocol_name)
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
        """
        This is called by Twisted, to tell the factory to set up a protocol.

        The default is usually okay, but we've overridden it here because
        we don't need the whole "multiple protocols per factory" thing, and
        we're doing some other Ultros-related stuff here too.
        """

        self.logger.debug(_("Entering setup method."))

        try:
            if self.protocol_class is None:
                self.logger.debug(_("First-time setup; not reloading."))
                current_protocol = importlib.import_module(
                    "system.protocols.%s.protocol" % self.ptype)
            else:
                del self.protocol
                self.logger.debug(_("Reloading module."))
                current_protocol = reload(self.protocol_class)

                if hasattr(current_protocol, "reload"):
                    current_protocol.reload()
            self.protocol_class = current_protocol
        except ImportError:
            self.logger.exception(
                _("Unable to import protocol %s for %s") %
                (self.ptype, self.name))
        else:
            if issubclass(current_protocol.Protocol, GenericProtocol):
                self.protocol = current_protocol.Protocol(self.name,
                                                          self,
                                                          self.config)
            else:
                raise TypeError(_("Protocol does not subclass the generic "
                                  "protocol class!"))

    def shutdown(self):
        self.shutting_down = True
        try:
            self.protocol.shutdown()
        except Exception:
            self.logger.exception(_("Error shutting down"))

    def buildProtocol(self, addr):
        """
        Another overridden standard Twisted function. We're just returning
        the current protocol here.
        """

        return self.protocol

    def clientConnectionLost(self, connector, reason):
        """
        Called when the client loses connection. Overridden here for
        reconnection purposes.
        """

        if hasattr(self.protocol, "on_connection_lost"):
            try:
                self.protocol.on_connection_lost()
            except Exception:
                self.logger.exception(_("Error calling \"connection lost\" "
                                        "callback"))

        if self.shutting_down:
            return

        self.logger.warn(_("Lost connection: %s") % reason.__str__())
        if self.r_on_drop:
            if self.attempts >= self.r_attempts:
                self.logger.error(_("Unable to connect after %s attempts, "
                                    "aborting.") % self.attempts)
                return
            self.attempts += 1
            self.logger.info(_("Reconnecting after %s seconds (attempt %s/%s)")
                             % (self.r_delay, self.attempts, self.r_attempts))
            reactor.callLater(self.r_delay, self.setup)

    def clientConnectionFailed(self, connector, reason):
        """
        Called when the client fails to connect. Overridden here for
        reconnection purposes.
        """

        if hasattr(self.protocol, "on_connection_failed"):
            try:
                self.protocol.on_connection_failed()
            except Exception:
                self.logger.exception(_("Error calling \"connection failed\" "
                                        "callback"))

        if self.shutting_down:
            return

        self.logger.warn(_("Connection failed: %s") % reason.__str__())
        if self.r_on_drop or self.reconnecting:
            if self.attempts >= self.r_attempts:
                self.logger.error(_("Unable to connect after %s attempts, "
                                    "aborting.") % self.attempts)
                return
            self.attempts += 1
            self.logger.info(_("Reconnecting after %s seconds (attempt %s/%s)")
                             % (self.r_delay, self.attempts, self.r_attempts))
            reactor.callLater(self.r_delay, self.setup)

    def clientConnected(self):
        if hasattr(self.protocol, "on_connected"):
            try:
                self.protocol.on_connected()
            except Exception:
                self.logger.exception(_("Error calling \"connected\" "
                                        "callback"))

        if self.r_reset:
            self.attempts = 0
