# coding=utf-8

import time
from system.protocols.irc.channel import Channel
from system.protocols.irc.user import User

from utils.log import getLogger
from system.event_manager import EventManager
from system.events import irc as irc_events

from twisted.words.protocols import irc
from twisted.internet import reactor, ssl


class Protocol(irc.IRCClient):
    factory = None
    config = None
    log = None
    event_manger = None

    networking = {}
    identity = {}

    nickname = ""

    channels = {}  # key is "#channel".lower()
    users = {}  # key is ident@host

    def __init__(self, factory, config):
        # Some notes for implementation..
        # Quakenet uses AUTH username password
        self.factory = factory
        self.config = config
        self.event_manager = EventManager.instance()
        self.log = getLogger("IRC")
        self.log.info("Setting up..")

        self.networking = config["network"]
        self.identity = config["identity"]

        self.nickname = self.identity["nick"]

        # TODO: Throw event (General, pre-connection)

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

        # TODO: Throw event (General, post-connection, pre-setup)

    def __call__(self):
        return self

    def receivedMOTD(self, motd):
        """ Called when we receive the MOTD. """
        self.log.info(" ===   MOTD   === ")
        for line in motd:
            self.log.info(line)
        self.log.info(" === END MOTD ===")

        event = irc_events.MOTDReceivedEvent(self, motd)
        self.event_manager.run_callback("IRC/MOTDReceived", event, True)

    def signedOn(self):
        """
         Called once we've connected and done our handshake with the IRC server
        """

        def do_sign_on(self):
            if self.identity["authentication"].lower() == "nickserv":
                self.msg(self.identity["auth_target"],
                         "IDENTIFY %s %s" % (self.identity["auth_name"],
                                             self.identity["auth_pass"]))
            elif self.identity["authentication"].lower() == "ns-old":
                self.msg(self.identity["auth_target"],
                         "IDENTIFY %s" % self.identity["auth_pass"])
            elif self.identity["authentication"].lower() == "auth":
                self.sendLine("AUTH %s %s" % (
                    self.identity["auth_name"], self.identity["auth_pass"]))
            elif self.identity["authentication"].lower() == "password":
                self.sendLine("PASS %s:%s" % (
                    self.identity["auth_name"], self.identity["auth_pass"]))

        def do_channel_joins(self):
            for channel in self.config["channels"]:
                self.join(channel["name"], channel["key"])

            # TODO: Throw event (General, post-setup)

        self.log.debug(
            "Scheduling Deferreds for signing on and joining channels")

        reactor.callLater(5, do_sign_on, self)
        reactor.callLater(10, do_channel_joins, self)

        # TODO: Throw event (General, pre-setup)

    def joined(self, channel):
        """ Called when we join a channel. """
        self.log.info("Joined channel: %s" % channel)

        # TODO: Channel objects
        event = irc_events.ChannelJoinedEvent(self, channel)
        self.event_manager.run_callback("IRC/ChannelJoined", event)

    def privmsg(self, user, channel, message):
        """ Called when we receive a message - channel or private. """
        self.log.info("<%s:%s> %s" % (user, channel, message))

        # TODO: Throw event (General, received message - normal, [target])

    def noticed(self, user, channel, message):
        """ Called when we receive a notice - channel or private. """
        self.log.info("-%s:%s- %s" % (user, channel, message))

        # TODO: Throw event (General, received message - notice, [target])

    def left(self, channel):
        """ Called when we part a channel.
        This could include opers using /sapart. """
        self.log.info("Parted channel: %s" % channel)

        event = irc_events.ChannelPartedEvent(self, channel)
        self.event_manager.run_callback("IRC/ChannelParted", event)

    def ctcpQuery(self, user, me,
                  messages):
        """ Called when someone does a CTCP query - channel or private.
        Needs some param analysis."""
        self.log.info("[%s] %s" % (user, messages))

        # TODO: Throw event (IRC, CTCP query)

    def modeChanged(self, user, channel, action, modes,
                    args):
        """ Called when someone changes a mode. Action is a bool specifying
        whether the mode was being set or unset.
            Will probably need to do some testing, mostly to see whether this
            is called for umodes as well. """
        self.log.info("%s sets mode %s: %s%s %s" % (
            user, channel, "+" if action else "-", modes, args))

        # TODO: Throw event (IRC, mode changed)

    def kickedFrom(self, channel, kicker,
                   message):
        """ Called when we get kicked from a channel. """
        self.log.info("Kicked from %s by %s: %s" % (channel, kicker, message))

        # TODO: Throw event (IRC, kicked from channel)

    def nickChanged(self,
                    nick):
        """ Called when our nick is forcibly changed. """
        self.log.info("Nick changed to %s" % nick)

        # TODO: Throw event (General, name changed)

    def userJoined(self, user,
                   channel):
        """ Called when someone else joins a channel we're in. """
        self.log.info("%s joined %s" % (user, channel))

        # TODO: Throw event (IRC, user joined channel)

    def userLeft(self, user,
                 channel):
        """ Called when someone else leaves a channel we're in. """
        self.log.info("%s parted %s" % (user, channel))

        # TODO: Throw event (IRC, user left channel)

    def userKicked(self, kickee, channel, kicker,
                   message):
        """ Called when someone else is kicked from a channel we're in. """
        self.log.info("%s was kicked from %s by %s: %s" % (
            kickee, channel, kicker, message))

        # TODO: Throw event (IRC, user kicked from channel)

    def irc_QUIT(self, user,
                 params):
        """ Called when someone else quits IRC. """
        quitmessage = params[0]
        self.log.info("%s has left IRC: %s" % (user, quitmessage))

        # TODO: Throw event (General, user disconnected)

    def topicUpdated(self, user, channel,
                     newTopic):
        """ Called when the topic is updated in a channel -
        also called when we join a channel. """
        self.log.info(
            "Topic for %s: %s (set by %s)" % (channel, newTopic, user))

        # TODO: Throw event (IRC, topic updated)

    def irc_NICK(self, prefix,
                 params):
        """ Called when someone changes their nick.
        Surprisingly, twisted doesn't have a handler for this. """

        oldnick = prefix.split("!", 1)[0]
        newnick = params[0]

        self.log.info("%s is now known as %s" % (oldnick, newnick))

        # TODO: Throw event (General, user changed their nick)

    def irc_RPL_WHOREPLY(self,
                         *nargs):
        """ Called when we get a WHO reply from the server.
        I'm seriously wondering if we even need this. """
        data = nargs[1]

        channel = data[1]
        ident = data[2]  # Starts with a ~ if there's no identd present
        host = data[3]
        server = data[4]
        nick = data[5]
        status = data[6].strip("G").strip("H").strip("*")
        gecos = data[7]  # Hops, realname

        # TODO: Throw event (IRC, WHO reply)

    def irc_RPL_ENDOFWHO(self,
                         *nargs):
        """ Called when the server's done spamming us with WHO replies. """
        data = nargs[1]
        channel = data[1]

        # TODO: Throw event (IRC, end of WHO reply)

    def irc_unknown(self, prefix, command, params):
        """ Packets that aren't handled elsewhere get passed to this function.
        """

        if command == "RPL_BANLIST":
            # This is a single entry in a channel's ban list.
            channel = params[1]
            mask = params[2]
            owner = params[3]
            btime = params[4]

        # TODO: Throw event (IRC, ban list)

        elif command == "RPL_ENDOFBANLIST":
            # Called when the server's done spamming us with the ban list
            channel = params[1]

        # TODO: Throw event (IRC, end of ban list)

        elif command == "RPL_NAMREPLY":
            # This is the response to a NAMES request.
            # Also includes some data that has nothing to do with channel names
            me, status, channel, names = params
            users = names.split()
            if status == "@":  # Secret channel
                pass
            elif status == "*":  # Private channel
                pass

        # TODO: Throw event (IRC, NAMES reply)

        elif command == "RPL_ENDOFNAMES":
            # Called when the server's done spamming us with NAMES replies.
            me, channel, message = params

        # TODO: Throw event (IRC, end of NAMES reply)

        elif command == "ERR_INVITEONLYCHAN":
            self.log.warn(
                "Unable to join %s - Channel is invite-only" % params[1])

        # TODO: Throw event (IRC, channel is invite-only)

        elif str(command) == "972":  # ERR_CANNOTDOCOMMAND
            pass  # Need to analyze the args of this.
            # Called when some command we attempted can't be done.

        # TODO: Throw event (IRC, cannot do command)

        elif str(command) == "333":  # Channel creation details
            self.log.info("%s created by %s (%s)" %
                          (params[1],
                           params[2],
                           time.strftime(
                               "%a, %d %b %Y %H:%M:%S",
                               time.localtime(
                                   float(params[3])
                               ))
                           ))

        # TODO: Throw event (IRC, channel creation details)

        elif str(command) in ["265", "266"]:  # RPL_LOCALUSERS, RPL_GLOBALUSERS
            self.log.info(params[
                3])  # Usually printed, these are purely informational

        # TODO: Throw event (IRC, LOCALUSERS reply and GLOBALUSERS reply)

        elif str(command) == "396":  # VHOST was set
            self.log.info("VHOST set to %s by %s" % (params[1], prefix))

        # TODO: Throw event (IRC, VHOST set)

        elif command == "PONG":
            pass  # Do we really need to print these?

        # TODO: Throw event (IRC, PONG) - Debatable

        else:
            self.log.debug(
                "Unhandled: %s | %s | %s" % (prefix, command, params))

            # TODO: Throw event (IRC, unhandled message event based on command)

    def self_join_channel(self, channel):
        self.channels[channel] = Channel(self, channel)
        # TODO: Run user_channel_join() on everyone in channel

    def self_part_channel(self, channel):
        for user in self.channels[channel].users:
            self.user_channel_part(user)
        del self.channels[channel]

    def user_channel_part(self, user, channel):
        # Get channel object
        chan = self.channels[channel]
        # Remove user from channel and channel from user
        user.remove_channel(chan)
        chan.remove_user(user)
        # Check if they've gone off our radar
        self.user_check_lost_track(user)

    def user_channel_join(self, nickname, ident, host, channel):
        # If the user is not known about, create them.
        key = "%s@%s" % (ident, host)
        user = None
        try:
            user = self.users[key]
        except KeyError:
            user = User(self, nickname, ident, host)
            self.users[key] = user
        # Add user to channel and channel to user
        chan = self.channels[channel]
        user.add_channel(chan)
        chan.add_user(user)

    def user_check_lost_track(self, user):
        if len(user.channels) == 0:
            del self.users["%s@%s" % (user.ident, user.host)]
            # TODO: Throw event: lost track of user
