# coding=utf-8

from utils.log import getLogger

from twisted.words.protocols import irc
from twisted.internet import reactor, ssl


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

    def receivedMOTD(self, motd):
        """ Called when we receive the MOTD. """
        self.log.info(" ===   MOTD   === ")
        for line in motd:
            self.log.info(line)
        self.log.info(" === END MOTD ===")

    def signedOn(self):
        """ Called once we've connected and done our handshake with the IRC server. """

        def doSignOn(self):
            if self.identity["authentication"].lower() == "nickserv":
                self.msg(self.identity["auth_target"], "IDENTIFY %s %s" % (self.identity["auth_name"], self.identity["auth_pass"]))
            elif self.identity["authentication"].lower() == "ns-old":
                self.msg(self.identity["auth_target"], "IDENTIFY %s" % self.identity["auth_pass"])
            elif self.identity["authentication"].lower() == "auth":
                self.sendLine("AUTH %s %s" % (self.identity["auth_name"], self.identity["auth_pass"]))
            elif self.identity["authentication"].lower() == "password":
                self.sendLine("PASS %s:%s" % (self.identity["auth_name"], self.identity["auth_pass"]))

        def doChannelJoins(self):
            for channel in self.config["channels"]:
                self.join(channel["name"], channel["key"])

        reactor.callLater(5, doSignOn, self)
        reactor.callLater(10, doChannelJoins, self)
        pass

    def joined(self, channel):
        """ Called when we join a channel. """
        self.log.info("Joined channel: %s" % channel)

    def privmsg(self, user, channel, message):
        """ Called when we receive a message - channel or private. """
        self.log.info("<%s:%s> %s" % (user, channel, message))

    def left(self, channel):
        """ Called when we part a channel. This could include opers using /sapart. """

        pass

    def ctcpQuery(self, user, me, messages):
        """ Called when someone does a CTCP query - channel or private. Needs some param analysis."""

        pass

    def modeChanged(self, user, channel, action, modes, args):
        """ Called when someone changes a mode. Action is a bool specifying whether the mode was being set or unset.
            Will probably need to do some testing, mostly to see whether this is called for umodes as well. """

        pass

    def kickedFrom(self, channel, kicker, message):
        """ Called when we get kicked from a channel. """

        pass

    def nickChanged(self, nick):
        """ Called when our nick is forcibly changed. """

        pass

    def userJoined(self, user, channel):
        """ Called when someone else joins a channel we're in. """

        pass

    def userLeft(self, user, channel):
        """ Called when someone else leaves a channel we're in. """

        pass

    def userKicked(self, kickee, channel, kicker, message):
        """ Called when someone else is kicked from a channel we're in. """

        pass

    def irc_QUIT(self, user, params):
        """ Called when someone else quits IRC. """

        quitMessage = params[0]

    def topicUpdated(self, user, channel, newTopic):
        """ Called when the topic is updated in a channel - also called when we join a channel. """

        pass

    def irc_NICK(self, prefix, params):
        """ Called when someone changes their nick. Surprisingly, twisted doesn't have a handler for this. """

        oldnick = prefix.split("!", 1)[0]
        newnick = params[0]

    def irc_RPL_WHOREPLY(self, *nargs):
        """ Called when we get a WHO reply from the server. I'm seriously wondering if we even need this. """
        data = nargs[1]

        channel = data[1]
        ident = data[2] # Starts with a ~ if there's no identd present
        host = data[3]
        server = data[4]
        nick = data[5]
        status = data[6].strip("G").strip("H").strip("*")
        gecos = data[7] # Hops, realname

    def irc_RPL_ENDOFWHO(self, *nargs):
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

        elif str(command) == "972":  # ERR_CANNOTDOCOMMAND
            pass  # Need to analyze the args of this. Called when some command we attempted can't be done.

        elif str(command) in ["265", "266"]:  # RPL_LOCALUSERS, RPL_GLOBALUSERS
            pass  # Usually just printed by clients, these are purely informational and probably not needed.

        elif not command == "PONG":
            pass  # Do we really need to print these?