# coding=utf-8
from twisted.internet import reactor, protocol
from twisted.internet.protocol import Factory
from twisted.words.protocols import irc

class Bot(irc.IRCClient):

    def __init__(self):
        pass

    def receivedMOTD(self, motd):
        """ Called when we receive the MOTD. """

        pass

    def connectionLost(self, reason):
        """ Supposedly called when we lose connection, but I'm really not sure if the factory handles that instead. """

        pass

    @property
    def nickname(self):
        """ This has to exist or Twisted can't get our nick. Needs reimplemented. """
        return None

    def signedOn(self):
        """ Called once we've connected and done our handshake with the IRC server. """

        pass

    def joined(self, channel):
        """ Called when we join a channel. """

        pass

    def privmsg(self, user, channel, msg):
        """ Called when we receive a message - channel or private. """

        pass

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

class BotFactory(protocol.ClientFactory):
    protocol = Bot

    def __init__(self):
        pass  # We should load settings and stuff here

    def clientConnectionLost(self, connector, reason):
        """ Called when the client loses connection """

        pass

    def clientConnectionFailed(self, connector, reason):
        """ Called when the client fails to connect """

        pass
