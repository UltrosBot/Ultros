# coding=utf-8
import importlib

from twisted.internet import reactor
from twisted.internet.error import AlreadyCancelled, AlreadyCalled, \
    ConnectionDone
from twisted.internet.protocol import ClientFactory
from twisted.python.failure import Failure

from system.protocols.generic.protocol import Protocol
from system.logging.logger import getLogger

__author__ = 'Gareth Coles'


class BaseFactory(ClientFactory):
    """
    A Twisted factory, for producing protocols. Now with less fuckery!

    Subclass this in your protocol's *factory.Factory* class, and use it to
    describe how your protocol is built and how it connects. If you find this
    confusing, you may want to read the other docstrings in this class, and
    take a look at the factory for the *irc* protocol.
    """

    protocol = None
    protocol_module = None

    reconnection_attempts = 0
    reconnection_config = None

    shutting_down = False
    task = None

    sent_warning = False

    @property
    def reconnection_config(self):
        c = self.factory_manager.main_config

        if "reconnections" in c:
            return self.factory_manager.main_config["reconnections"]
        elif not self.sent_warning:
            self.sent_warning = True
            self.logger.warn(
                "Unable to find a \"reconnections\" section in settings.yml - "
                "Please add one and ensure that it is configured to your needs"
            )
            return {}

    def __init__(self, protocol_name, config, factory_manager):
        self.name = protocol_name
        self.config = config
        self.factory_manager = factory_manager

        self.logger = getLogger("F: {}".format(self.name))

    # Custom Ultros functions - must be overridden

    def connect(self):
        """
        Called to begin the connection - this is only called once.

        In this function, you should read whatever you need from your config
        file to work out how to connect, and then use the reactor to do so,
        passing *self* in as the factory. For example:

        >>> reactor.connectTCP(
        ...     self.config["network"]["hostname"],
        ...     self.config["network"]["port"],
        ...     self,
        ...     self.config["network"]["timeout"],
        ...     bindAddress=("0.0.0.0", 0)
        ... )
        >>>

        You **must** override this method, or your factory will not work.

        Return True if you were able to initiate the connection, or False
        if not.

        :returns: Whether the connection was initiated or not
        :rtype: bool
        """
        raise NotImplementedError()

    # Custom Ultros functions - Not necessary to override in most cases

    def load_module(self):
        """
        Load the protocol module, reloading if it's already loaded.

        If you use the standard Ultros naming scheme, then you won't need to
        override this. For reference, this function expects your protocol to
        reside in *system.protocols.[name].protocol*.
        """

        if "main" not in self.config:
            raise KeyError(
                "Protocol configuration is missing a \"main\" section"
            )

        if "protocol-type" not in self.config["main"]:
            raise KeyError(
                "Protocol configuration is missing a \"protocol-type\" value "
                "in the \"main\" section"
            )

        protocol_type = self.config["main"]["protocol-type"]

        if self.protocol_module is None:
            self.logger.debug("First-time setup, not reloading")
            self.protocol_module = importlib.import_module(
                "system.protocols.{}.protocol".format(
                    protocol_type
                )
            )
        else:
            self.logger.debug("Reloading module")
            try:
                self.protocol_module = reload(self.protocol_module)
            except Exception:
                self.protocol_module = None
                raise

        if not issubclass(self.protocol_module.Protocol, Protocol):
            self.protocol_module = None
            raise TypeError(
                "Protocol \"{}\" does not subclass the generic protocol "
                "class!".format(
                    protocol_type
                )
            )

    def get_reconnect_option(self, key, default=None):
        """
        Get a specific reconnect option from the configurations

        This will try the protocol-specific config, falling back to the
        global configuration, and then to the default value as supplied, in
        that order.
        """

        if "reconnections" in self.config:
            d = self.config["reconnections"]

            if key not in d:
                d = self.reconnection_config
        else:
            d = self.reconnection_config

        return d.get(key, default)

    def maybe_reconnect(self, connector, reason):
        """
        Check whether a reconnection is appropriate, and perform it if so

        This will check the configuration as specified in
        `get_reconnect_option`, and conditionally reconnect (or not) as
        configured.
        """

        if self.shutting_down:
            return

        if self.get_reconnect_option("on-{}".format(reason), False):
            if self.get_reconnect_option("attempts", 5) > 0:
                if (
                        self.reconnection_attempts >=
                        self.get_reconnect_option("attempts", 5)
                ):
                    self.logger.warn(
                        "Unable to connect after {} attempts, aborting".format(
                            self.reconnection_attempts
                        )
                    )
                    return

            self.reconnection_attempts += 1

            max_delay = self.get_reconnect_option("max_delay", 300)

            delay = self.get_reconnect_option("delay", 10)
            delay *= self.reconnection_attempts

            if delay > max_delay:
                delay = max_delay

            self.logger.info(
                "Connecting after {} seconds (attempt {}/{})".format(
                    delay, self.reconnection_attempts,
                    self.get_reconnect_option("attempts", 5) or "infinite"
                )
            )

            return reactor.callLater(delay, connector.connect)

    def shutdown(self):
        """
        Shut down the factory, and thus the protocol it's in charge of.

        This is called when the bot is shutting down, or just if a user
        wants to shut down the protocol. It will call the
        *protocol.shutdown()* method and prevent reconnections.
        """

        self.shutting_down = True

        try:
            if self.task is not None:
                self.task.cancel()
        except (AlreadyCalled, AlreadyCancelled):
            pass
        except Exception:
            self.logger.exception("Failed to cancel task")

        if self.protocol:
            try:
                self.protocol.shutdown()
            except Exception:
                self.logger.exception("Error shutting down protocol")

            self.protocol = None

    # Base Twisted functions - override if necessary

    def buildProtocol(self, addr):
        """
        Build a protocol instance for Twisted to use.

        If your protocol uses the Ultros default *__init__* function, you will
        likely not need to override this. For reference, the arguments expected
        for that function are **(*name*, *factory*, *config*)**.
        """

        try:
            self.load_module()
            self.protocol = self.protocol_module.Protocol(
                self.name, self, self.config
            )
            return self.protocol
        except Exception:
            self.protocol = None
            self.factory_manager.remove_protocol(self.name)
            raise

    # Base Twisted functions - override if necessary and call superclass

    def clientConnected(self):
        """
        Called when the protocol makes a successful connection.

        If for some reason you aren't using the reactor for your connection,
        then you may want to call this in your protocol manually, as it will
        reset the reconnection counter as appropriate.
        """

        if self.reconnection_config["reset-on-success"]:
            self.reconnection_attempts = 0

    def clientConnectionFailed(self, connector, reason):
        """
        Called when the protocol failed to connect.

        If for some reason you aren't using the reactor for your connection,
        then you may want to call this in your protocol manually, as it
        automatically handles reconnections as appropriate.
        """

        self.logger.warn("Connection failed: {}".format(reason))

        self.task = self.maybe_reconnect(connector, "failure")

    def clientConnectionLost(self, connector, reason):
        """
        Called when the protocol connected, and then lost connection later.

        If for some reason you aren't using the reactor for your connection,
        then you may want to call this in your protocol manually, as it
        automatically handles reconnections as appropriate.
        """

        if isinstance(reason, Failure):
            if isinstance(reason.value, ConnectionDone):
                self.logger.info("Disconnected: Connection done")
            else:
                self.logger.warn("Connection lost: {}".format(reason.value))
        else:
            self.logger.warn("Connection lost: {}".format(reason))

        self.task = self.maybe_reconnect(connector, "drop")
