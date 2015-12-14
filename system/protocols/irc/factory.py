# coding=utf-8
from twisted.internet import reactor

from system.protocols.generic.factory import BaseFactory

__author__ = 'Gareth Coles'


class Factory(BaseFactory):
    def connect(self):
        try:
            from twisted.internet import ssl
            use_ssl = True
        except ImportError:
            ssl = None
            use_ssl = False
            self.logger.exception(
                "Unable to import the SSL library. SSL will not be available."
            )

        networking = self.config["network"]

        binding = networking.get("bindaddr", None)
        bindaddr = None

        if binding:
            bindaddr = (binding, 0)

        if networking["ssl"] and not use_ssl:
            self.logger.error(
                "SSL is not available but was requested in the configuration."
            )
            self.logger.error(
                "This protocol will be unavailable until SSL is fixed, or you "
                "disable it in the configuration."
            )

            return False

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

        return True
