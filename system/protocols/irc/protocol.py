# coding=utf-8

from utils.log import getLogger
from twisted.words.protocols import irc
from twisted.internet import reactor, ssl
import time


class Protocol(irc.IRCClient):

    factory = None
    config = None
    log = None

    networking = {}
    identity = {}

    nickname = ""

    def __init__(self, factory, config):
        # Some notes for implementation..
        #  reactor.connectSSL(host, port, factory, ssl.ClientContextFactory()) can be used for SSL
        #  Quakenet uses AUTH username password
        self.factory = factory
        self.config = config
        self.log = getLogger("IRC")
        self.log.info("Setting up..")

        self.networking = config["network"]
        self.identity = config["identity"]

        self.nickname = self.identity["nick"]

        if self.networking["ssl"]:
            self.log.debug("Connecting with SSL")
            reactor.connectSSL(
                self.networking["address"],
                self.networking["port"],
                self.factory,
                ssl.ClientContextFactory(),
                120
            )
        else:
            self.log.debug("Connecting without SSL")
            reactor.connectTCP(
                self.networking["address"],
                self.networking["port"],
                self.factory,
                120
            )

    def __call__(self):
        return self

    def receivedMOTD(self, motd):  # Not strictly PEP but Twisted demands capital letters
        """ Called when we receive the MOTD. """
        self.log.info(" ===   MOTD   === ")
        for line in motd:
            self.log.info(line)
        self.log.info(" === END MOTD ===")

    def signedOn(self):  # Not strictly PEP but Twisted demands capital letters
        """ Called once we've connected and done our handshake with the IRC server. """

        def do_sign_on(self):
            if self.identity["authentication"].lower() == "nickserv":
                self.msg(self.identity["auth_target"], "IDENTIFY %s %s" % (self.identity["auth_name"],
                                                                           self.identity["auth_pass"]))
            elif self.identity["authentication"].lower() == "ns-old":
                self.msg(self.identity["auth_target"], "IDENTIFY %s" % self.identity["auth_pass"])
            elif self.identity["authentication"].lower() == "auth":
                self.sendLine("AUTH %s %s" % (self.identity["auth_name"], self.identity["auth_pass"]))
            elif self.identity["authentication"].lower() == "password":
                self.sendLine("PASS %s:%s" % (self.identity["auth_name"], self.identity["auth_pass"]))

        def do_channel_joins(self):
            for channel in self.config["channels"]:
                self.join(channel["name"], channel["key"])

        self.log.debug("Scheduling Deferreds for signing on and joining channels")

        reactor.callLater(5, do_sign_on, self)
        reactor.callLater(10, do_channel_joins, self)

    def joined(self, channel):
        """ Called when we join a channel. """
        self.log.info("Joined channel: %s" % channel)

    def privmsg(self, user, channel, message):
        """ Called when we receive a message - channel or private. """
        self.log.info("<%s:%s> %s" % (user, channel, message))

    def noticed(self, user, channel, message):
        """ Called when we receive a notice - channel or private. """
        self.log.info("-%s:%s- %s" % (user, channel, message))

    def left(self, channel):
        """ Called when we part a channel. This could include opers using /sapart. """
        self.log.info("Parted channel: %s" % channel)

    def ctcpQuery(self, user, me, messages):  # Not strictly PEP but Twisted demands capital letters
        """ Called when someone does a CTCP query - channel or private. Needs some param analysis."""
        self.log.info("[%s] %s" % (user, messages))

    def modeChanged(self, user, channel, action, modes, args):  # Not strictly PEP but Twisted demands capital letters
        """ Called when someone changes a mode. Action is a bool specifying whether the mode was being set or unset.
            Will probably need to do some testing, mostly to see whether this is called for umodes as well. """
        self.log.info("%s sets mode %s: %s%s %s" % (user, channel, "+" if action else "-", modes, args))

    def kickedFrom(self, channel, kicker, message):  # Not strictly PEP but Twisted demands capital letters
        """ Called when we get kicked from a channel. """
        self.log.info("Kicked from %s by %s: %s" % (channel, kicker, message))

    def nickChanged(self, nick):  # Not strictly PEP but Twisted demands capital letters
        """ Called when our nick is forcibly changed. """
        self.log.info("Nick changed to %s" % nick)

    def userJoined(self, user, channel):  # Not strictly PEP but Twisted demands capital letters
        """ Called when someone else joins a channel we're in. """
        self.log.info("%s joined %s" % (user, channel))

    def userLeft(self, user, channel):  # Not strictly PEP but Twisted demands capital letters
        """ Called when someone else leaves a channel we're in. """
        self.log.info("%s parted %s" % (user, channel))

    def userKicked(self, kickee, channel, kicker, message):  # Not strictly PEP but Twisted demands capital letters
        """ Called when someone else is kicked from a channel we're in. """
        self.log.info("%s was kicked from %s by %s: %s" % (kickee, channel, kicker, message))

    def irc_QUIT(self, user, params):  # Not strictly PEP but Twisted demands capital letters
        """ Called when someone else quits IRC. """
        quitMessage = params[0]
        self.log.info("%s has left IRC: %s" % (user, quitMessage))

    def topicUpdated(self, user, channel, newTopic):  # Not strictly PEP but Twisted demands capital letters
        """ Called when the topic is updated in a channel - also called when we join a channel. """
        self.log.info("Topic for %s: %s (set by %s)" % (channel, newTopic, user))
        pass

    def irc_NICK(self, prefix, params):  # Not strictly PEP but Twisted demands capital letters
        """ Called when someone changes their nick. Surprisingly, twisted doesn't have a handler for this. """

        oldnick = prefix.split("!", 1)[0]
        newnick = params[0]

        self.log.info("%s is now known as %s" % (oldnick, newnick))

    def irc_RPL_WHOREPLY(self, *nargs):  # Not strictly PEP but Twisted demands capital letters
        """ Called when we get a WHO reply from the server. I'm seriously wondering if we even need this. """
        data = nargs[1]

        channel = data[1]
        ident = data[2]  # Starts with a ~ if there's no identd present
        host = data[3]
        server = data[4]
        nick = data[5]
        status = data[6].strip("G").strip("H").strip("*")
        gecos = data[7]  # Hops, realname

    def irc_RPL_ENDOFWHO(self, *nargs):  # Not strictly PEP but Twisted demands capital letters
        """ Called when the server's done spamming us with WHO replies. """
        data = nargs[1]
        channel = data[1]

    def irc_unknown(self, prefix, command, params):
        """ Packets that aren't handled elsewhere get passed to this function. """

        if command == "RPL_BANLIST":
            # This is a single entry in a channel's ban list.
            channel = params[1]
            mask = params[2]
            owner = params[3]
            btime = params[4]

        elif command == "RPL_ENDOFBANLIST":
            # Called when the server's done spamming us with the ban list we requested.
            channel = params[1]

        elif command == "RPL_NAMREPLY":
            # This is the response to a NAMES request.
            # Also includes some data that has nothing to do with channel names at all.
            me, status, channel, names = params
            users = names.split()
            if status == "@":  # Secret channel
                pass
            elif status == "*":  # Private channel
                pass

        elif command == "RPL_ENDOFNAMES":
            # Called when the server's done spamming us with NAMES replies.
            me, channel, message = params

        elif command == "ERR_INVITEONLYCHAN":
            self.log.warn("Unable to join %s - Channel is invite-only" % params[1])

        elif str(command) == "972":  # ERR_CANNOTDOCOMMAND
            pass  # Need to analyze the args of this. Called when some command we attempted can't be done.

        elif str(command) == "333":  # Channel creation details
            self.log.info("%s created by %s (%s)" % (params[1],
                                                     params[2],
                                                     time.strftime("%a, %d %b %Y %H:%M:%S",
                                                                   time.localtime(
                                                                       float(params[3])
                                                                   ))
                                                     ))

        elif str(command) in ["265", "266"]:  # RPL_LOCALUSERS, RPL_GLOBALUSERS
            self.log.info(params[3])  # Usually printed, these are purely informational and might not be needed.

        elif str(command) == "396":  # VHOST was set
            self.log.info("VHOST set to %s by %s" % (params[1], prefix))

        elif command == "PONG":
            pass  # Do we really need to print these?

        else:
            self.log.debug("Unhandled: %s | %s | %s" % (prefix, command, params))
