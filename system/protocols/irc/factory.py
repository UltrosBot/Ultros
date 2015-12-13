# coding=utf-8
from twisted.internet import reactor

from system.protocols.generic.factory import BaseFactory

__author__ = 'Gareth Coles'


class Factory(BaseFactory):
    ssl = False

    def connect(self):
        try:
            from twisted.internet import ssl
            self.ssl = True
        except ImportError:
            ssl = None
            self.ssl = False
            self.logger.exception(
                "Unable to import the SSL library. SSL will not be available."
            )

        networking = self.config["network"]

        binding = networking.get("bindaddr", None)
        bindaddr = None

        if binding:
            bindaddr = (binding, 0)

        if networking["ssl"] and not ssl:
            self.logger.error(
                "SSL is not available but was requested in the configuration."
            )
            self.logger.error(
                "This protocol will be unavailable until SSL is fixed, or you "
                "disable it in the configuration."
            )

            self.factory_manager.remove_protocol(self.name)
            return

        if networking["ssl"]:
            self.logger.debug("Connecting with SSL")

            reactor.connectSSL(
                networking["address"],
                networking["port"],
                self,
                ssl.ClientContextFactory(),
                120,
                bindAddress=bindaddr
            )
        else:
            self.logger.debug("Connecting without SSL")

            reactor.connectTCP(
                networking["address"],
                networking["port"],
                self,
                120,
                bindAddress=bindaddr
            )
