# coding=utf-8

import time
import logging
import re

from system.protocols.irc.channel import Channel
from system.protocols.irc.rank import Ranks
from system.protocols.irc.user import User
from utils.irc import IRCUtils

from utils.log import getLogger
from utils.misc import output_exception
from system.event_manager import EventManager
from system.command_manager import CommandManager
from system.events import irc as irc_events
from system.events import general as general_events

from twisted.words.protocols import irc
from twisted.internet import reactor

from kitchen.text.converters import to_bytes


class Protocol(irc.IRCClient):
    factory = None
    config = None
    log = None
    event_manager = None

    networking = {}
    identity = {}

    nickname = ""

    channels = {}  # key is lowercase "#channel" - use get/set/del_channel()
    # TODO: Make users a set()?
    users = []
    own_user = None

    ssl = False

    def __init__(self, factory, config):
        self.log = getLogger("IRC")
        self.log.info("Setting up..")

        try:
            from twisted.internet import ssl
            self.ssl = True
        except ImportError:
            ssl = False
            self.ssl = False
            self.log.warn("Unable to import the SSL library. "
                          "SSL will not be available.")
            output_exception(self.log, logging.WARN)
        except ImportError:
            ssl = False
            self.ssl = False
            self.log.warn("Unable to import the SSL library. "
                          "SSL will not be available.")

            output_exception(self.log, logging.WARN)
        else:
            self.ssl = True

        self.factory = factory
        self.config = config
        self.event_manager = EventManager.instance()
        self.command_manager = CommandManager.instance()
        self.utils = IRCUtils(self.log)
        # Three dicts for easier lookup
        self.ranks = Ranks()
        # Default prefixes in case the server doesn't send us a RPL_ISUPPORT
        self.ranks.add_rank("o", "@", 0)
        self.ranks.add_rank("v", "+", 1)

        self.networking = config["network"]
        self.identity = config["identity"]
        self.control_chars = config["control_chars"]

        if self.identity["authentication"].lower() == "password":
            self.password = "%s:%s" % (self.identity["auth_name"],
                                       self.identity["auth_pass"])

        self.nickname = self.identity["nick"]

        event = general_events.PreConnectEvent(self, config)
        self.event_manager.run_callback("PreConnect", event)

        if self.networking["ssl"] and not self.ssl:
            self.log.error("SSL is not available but was requested in the "
                           "configuration.")
            self.log.error("IRC will be unavailable until SSL is fixed or is "
                           "disabled in the configuration.")

            # Clean up so everything can be garbage-collected
            self.factory.manager.remove_protocol("irc")

            del self.event_manager
            del self.utils
            del self.ranks
            del self.log
            del self.factory
            del self.config

            return

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

        event = general_events.PostConnectEvent(self, config)
        self.event_manager.run_callback("PostConnect", event)

    def send_unicode_line(self, data):
        self.sendLine(to_bytes(data))

    def send_unicode_msg(self, target, data, length=None):
        self.msg(to_bytes(target), to_bytes(data), length)

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

        # Reset users and channels when we connect, in case we still have them
        # from a previous connection.
        self.own_user = None
        self.users = []
        self.channels = {}

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

            event = general_events.PostSetupEvent(self, self.config)
            self.event_manager.run_callback("PostSetup", event)

        self.log.debug(
            "Scheduling Deferreds for signing on and joining channels")

        reactor.callLater(5, do_sign_on, self)
        reactor.callLater(10, do_channel_joins, self)

        event = general_events.PreSetupEvent(self, self.config)
        self.event_manager.run_callback("PreSetup", event)

    def joined(self, channel):
        """ Called when we join a channel. """
        self.log.info("Joined channel: %s" % channel)
        chan_obj = Channel(self, channel)
        self.set_channel(channel, chan_obj)
        # User-tracking stuff
        self.send_who(channel)

        event = irc_events.ChannelJoinedEvent(self, chan_obj)
        self.event_manager.run_callback("IRC/ChannelJoined", event)

    def left(self, channel):
        """ Called when we part a channel.
        This could include opers using /sapart. """
        self.log.info("Parted channel: %s" % channel)
        chan_obj = self.get_channel(channel)
        # User-tracking stuff:
        self.self_part_channel(chan_obj)

        event = irc_events.ChannelPartedEvent(self, chan_obj)
        self.event_manager.run_callback("IRC/ChannelParted", event)

    def handle_command(self, source, target, message):
        """
        Handles checking a message for a command.
        """

        cc = self.control_chars.replace("{NICK}", self.nickname).lower()

        if message.lower().startswith(cc):  # It's a command!
            # Some case-insensitive replacement here.
            regex = re.compile(re.escape(cc), re.IGNORECASE)
            replaced = regex.sub("", message, count=1)

            split = replaced.split()
            command = split[0]
            args = split[1:]

            self.log.info("%s ran the %s command in %s" % (source.nickname,
                                                           command, target))

            result = self.command_manager.run_command(command, source, target,
                                                      self, args)
            a, b = result
            if a:
                pass  # Command ran successfully
            else:  # There's a problem
                if b is True:  # Unable to authorize
                    self.log.warn("%s is not authorized to use the %s "
                                  "command"
                                  % (source.nickname, command))
                elif b is None:  # Command not found
                    self.log.debug("Command not found: %s" % command)
                    return False
                else:  # Exception occured
                    self.log.warn("An error occured while running the %s "
                                  "command: %s" % (command, b))
            return True
        return False

    def privmsg(self, user, channel, message):
        """ Called when we receive a message - channel or private. """

        user_obj = None
        try:
            user_obj = self._get_user_from_user_string(user)
        except:
            # Privmsg from the server itself and things (if that happens)
            self.log.debug("Notice from irregular user: %s" % user)
            user_obj = User(self, nickname=user, is_tracked=False)
        channel_obj = None
        if self.utils.compare_nicknames(channel, self.nickname):
            channel_obj = user_obj
        else:
            channel_obj = self.get_channel(channel)

        if not self.handle_command(user_obj, chan_obj, message):
            event = general_events.PreMessageReceived(self, user_obj, chan_obj,
                                                      message, "message",
                                                      printable=True)
            self.event_manager.run_callback("PreMessageReceived", event)
            if event.printable:
                self.log.info("<%s:%s> %s" % (user_obj.nickname, channel,
                                              event.message))

            second_event = general_events.MessageReceived(self, user_obj,
                                                          chan_obj,
                                                          event.message,
                                                          "message")
            self.event_manager.run_callback("MessageReceived", second_event)

    def noticed(self, user, channel, message):
        """ Called when we receive a notice - channel or private. """
        user_obj = None
        try:
            user_obj = self._get_user_from_user_string(user)
        except:
            # Notices from the server itself and things
            self.log.debug("Notice from irregular user: %s" % user)
            user_obj = User(self, nickname=user, is_tracked=False)
        channel_obj = None
        if self.utils.compare_nicknames(channel, self.nickname):
            channel_obj = user_obj
        else:
            channel_obj = self.get_channel(channel)

        if channel != self.nickname:
            # This is not a PM.
            chan_obj = self.get_channel(channel)

        event = general_events.PreMessageReceived(self, user_obj, chan_obj,
                                                  message, "notice",
                                                  printable=True)
        self.event_manager.run_callback("PreMessageReceived", event)
        if event.printable:
            self.log.info("-%s:%s- %s" % (user, channel, event.message))

        second_event = general_events.MessageReceived(self, user_obj, chan_obj,
                                                      event.message, "notice")
        self.event_manager.run_callback("MessageReceived", second_event)

    def ctcpQuery(self, user, me, messages):
        """ Called when someone does a CTCP query - channel or private.
        Needs some param analysis."""
        self.log.info("[%s] %s" % (user, messages))
        user_obj = None
        try:
            user_obj = self._get_user_from_user_string(user)
        except:
            # CTCP from the server itself and things (if that happens)
            self.log.debug("CTCP from irregular user: %s" % user)
            user_obj = User(self, nickname=user, is_tracked=False)
        channel_obj = None
        if self.utils.compare_nicknames(channel, self.nickname):
            channel_obj = user_obj
        else:
            channel_obj = self.get_channel(channel)

        event = irc_events.CTCPQueryEvent(self, user_obj, messages)
        self.event_manager.run_callback("IRC/CTCPQueryReceived", event)

    def modeChanged(self, user, channel, action, modes, args):
        """
        Called when someone changes a mode. Action is a bool specifying
        whether the mode was being set or unset.
        If it's a usermode, channel is the user being changed.

        Note: If it's a user-mode, channel_obj is set to None.
        """
        self.log.info("%s sets mode %s: %s%s %s" % (
            user, channel, "+" if action else "-", modes, args))

        # Get user/channel objects
        try:
            user_obj = self._get_user_from_user_string(user)
        except:
            # Mode change from the server itself and things
            self.log.debug("Mode change from irregular user: %s" % user)
            user_obj = User(self, nickname=user, is_tracked=False)
        # Note: Unlike in privmsg/notice/ctcpQuery, channel_obj = None when
        # the target is ourself, rather than a user object. Perhaps this should
        # be changed for clarity?
        channel_obj = None
        if not self.utils.compare_nicknames(self.nickname, channel):
            channel_obj = self.get_channel(channel)

        # Handle the mode changes
        for x in xrange(len(modes)):
            if channel_obj is None:
                # User mode (almost definitely always ourself)
                # TODO: Handle this (usermodes)
                pass
            elif modes[x] in self.ranks.modes:
                # Rank channel mode
                user_obj = self.get_user(args[x])
                if user_obj:
                    rank = self.ranks.by_mode(modes[x])
                    if action:
                        user_obj.add_rank_in_channel(channel, rank)
                    else:
                        user_obj.remove_rank_in_channel(channel, rank)
                else:
                    self.log.warning(
                        "Rank mode %s set on invalid user %s in channel %s"
                        % (modes[x], args[x], channel))
            else:
                # Other channel mode
                if action:
                    channel_obj.set_mode(modes[x], args[x])
                else:
                    channel_obj.remove_mode(modes[x])

        event = irc_events.ModeChangedEvent(self, user_obj, channel_obj,
                                            action, modes, args)
        self.event_manager.run_callback("IRC/ModeChanged", event)

    def kickedFrom(self, channel, kicker, message):
        """ Called when we get kicked from a channel. """
        self.log.info("Kicked from %s by %s: %s" % (channel, kicker, message))

        user_obj = self.get_user(nickname=kicker)
        chan_obj = self.get_channel(channel)
        # User-tracking stuff:
        self.self_part_channel(channel_obj)

        event = irc_events.KickedEvent(self, chan_obj, user_obj, message)
        self.event_manager.run_callback("IRC/SelfKicked", event)

    def nickChanged(self, nick):
        """ Called when our nick is forcibly changed. """
        self.log.info("Nick changed to %s" % nick)

        event = general_events.NameChangedSelf(self, nick)
        self.event_manager.run_callback("NameChangedSelf", event)

    def userJoined(self, user, channel):
        """ Called when someone else joins a channel we're in. """
        self.log.info("%s joined %s" % (user.nickname, channel))
        # Note: User tracking is done in irc_JOIN rather than here

        event = irc_events.UserJoinedEvent(self, channel, user)
        self.event_manager.run_callback("IRC/UserJoined", event)

    def irc_JOIN(self, prefix, params):
        """ Called on any join message
        :param prefix: The user joining
        :param params: The channel(s?) joined
        """
        # irc.IRCClient.irc_JOIN(self, prefix, params)
        # Removed as we can do this better than the library  -- g
        # For some reason, userJoined only gives the user's nick, so we do
        # user tracking here

        nickname, ident, host = self.utils.split_hostmask(prefix)
        if self.utils.compare_nicknames(nickname, self.nickname):
            if self.own_user is None:
                # User-tracking stuff
                self.own_user = User(self,
                                     nickname,
                                     ident,
                                     host,
                                     is_tracked=True)
                self.users.append(self.own_user)
        else:

        # There will only ever be one channel, so just get that. No need to
        # iterate.
        channel = params[-1]

        chan = self.get_channel(channel)

        if not self.utils.compare_nicknames(nickname, self.nickname):
            user = self.user_join_channel(nickname, ident, host, chan)

            # Since we're using our own function and the library doesn't
            # actually do anything with this, we can simply supply the
            # user and channel objects.
            self.userJoined(user, chan)
        else:
            self.joined(channel)

    def userLeft(self, user, channel):
        """ Called when someone else leaves a channel we're in. """
        self.log.info("%s parted %s" % (user, channel))
        chan_obj = self.get_channel(channel)
        user_obj = self.get_user(nickname=user)
        # User-tracking stuff
        self.user_channel_part(user_obj, chan_obj)

        event = irc_events.UserPartedEvent(self, chan_obj, user_obj)
        self.event_manager.run_callback("IRC/UserParted", event)

    def userKicked(self, kickee, channel, kicker, message):
        """ Called when someone else is kicked from a channel we're in. """
        self.log.info("%s was kicked from %s by %s: %s" % (
            kickee, channel, kicker, message))
        kickee_obj = self.get_user(nickname=kickee)
        kicker_obj = self.get_user(nickname=kicker)
        channel_obj = self.get_channel(channel)
        # User-tracking stuff
        self.user_channel_part(kickee_obj, chan_obj)

        event = irc_events.UserKickedEvent(self, chan_obj, kickee_obj,
                                           kicker_obj, message)
        self.event_manager.run_callback("IRC/UserKicked", event)

    def irc_QUIT(self, user, params):
        """ Called when someone else quits IRC. """
        quitmessage = params[0]
        self.log.info("%s has left IRC: %s" % (user, quitmessage))
        # User-tracking stuff
        user_obj = self.get_user(fullname=user)
        temp_chans = set(user_obj.channels)
        for channel in temp_chans:
            self.user_channel_part(user_obj, channel)

        event = general_events.UserDisconnected(self, user_obj)
        self.event_manager.run_callback("UserDisconnected", event)

    def topicUpdated(self, user, channel, newTopic):
        """ Called when the topic is updated in a channel -
        also called when we join a channel. """
        self.log.info(
            "Topic for %s: %s (set by %s)" % (channel, newTopic, user))

        user_obj = self.get_user(nickname=user) or User(self, nickname=user,
                                                        is_tracked=False)
        chan_obj = self.get_channel(channel) or Channel(self, channel)

        event = irc_events.TopicUpdatedEvent(self, chan_obj, user_obj,
                                             newTopic)
        self.event_manager.run_callback("IRC/TopicUpdated", event)

    def irc_NICK(self, prefix, params):
        """ Called when someone changes their nick.
        Surprisingly, twisted doesn't have a handler for this. """

        oldnick = prefix.split("!", 1)[0]
        newnick = params[0]

        user_obj = self.get_user(nickname=oldnick)
        user_obj.nickname = newnick

        self.log.info("%s is now known as %s" % (oldnick, newnick))

        event = general_events.NameChanged(self, user_obj, oldnick)
        self.event_manager.run_callback("NameChanged", event)

    def irc_RPL_WHOREPLY(self, *nargs):
        """ Called when we get a WHO reply from the server.
        I'm seriously wondering if we even need this. """
        data_ = nargs[1]

        channel = data_[1]
        ident = data_[2]  # Starts with a ~ if there's no identd present
        host = data_[3]
        server = data_[4]
        nick = data_[5]
        status = data_[6]  # .strip("G").strip("H").strip("*")
        gecos = data_[7]  # Hops, realname

        # User-tracking stuff
        try:
            chan_obj = self.get_channel(channel)
            self.channel_who_response(nick,
                                      ident,
                                      host,
                                      server,
                                      status,
                                      gecos,
                                      chan_obj)
        except KeyError:
            # We got a WHO reply for a channel we're not in - doesn't matter
            #   for user-tracking purposes.
            pass
        else:
            user_obj = self.get_user(nickname=nick)
            data = {"ident": ident, "host": host, "server": server,
                    "status": status, "gecos": gecos}

            event = irc_events.WHOReplyEvent(self, chan_obj, user_obj, data)
            self.event_manager.run_callback("IRC/WHOReply", event)

    def irc_RPL_ENDOFWHO(self, *nargs):
        """ Called when the server's done spamming us with WHO replies. """
        data_ = nargs[1]
        channel = data_[1]

        try:
            chan_obj = self.get_channel(channel)
        except KeyError:
            pass
        else:
            event = irc_events.WHOReplyEndEvent(self, chan_obj)
            self.event_manager.run_callback("IRC/EndOfWHO", event)

    def irc_RPL_ISUPPORT(self, prefix, params):
        irc.IRCClient.irc_RPL_ISUPPORT(self, prefix, params)
        for param in params[1:-1]:
            self.log.debug("RPL_ISUPPORT received: %s" % param)
            prm = param.split("=")[0].strip("-")
            # prm is the param changed - don't bother parsing the value since
            # it can be grabbed from self.supported with this:
            # self.supported.getFeature(prm)
            if prm == "CASEMAPPING":
                self.utils.case_mapping =\
                    self.supported.getFeature("CASEMAPPING")[0]  # Tuple
            elif prm == "PREFIX":
                # Remove the default prefixes before storing the new ones
                self.ranks = Ranks()
                for k, v in self.supported.getFeature("PREFIX").iteritems():
                    self.ranks.add_rank(k, v[0], v[1])

        event = irc_events.ISUPPORTReplyEvent(self, prefix, params)
        self.event_manager.run_callback("IRC/ISUPPORT", event)

    def irc_unknown(self, prefix, command, params):
        """ Packets that aren't handled elsewhere get passed to this function.
        """

        if command == "RPL_BANLIST":
            # This is a single entry in a channel's ban list.
            _, channel, mask, owner, btime = params
            chan_obj = self.get_channel(channel)

            event = irc_events.BanListEvent(self, chan_obj, mask, owner, btime)
            self.event_manager.run_callback("IRC/BanListReply", event)

        elif command == "RPL_ENDOFBANLIST":
            # Called when the server's done spamming us with the ban list
            channel = params[1]
            chan_obj = self.get_channel(channel)

            event = irc_events.BanListEndEvent(self, chan_obj)
            self.event_manager.run_callback("IRC/EndOfBanList", event)

        elif command == "RPL_NAMREPLY":
            # This is the response to a NAMES request.
            # Also includes some data that has nothing to do with channel names
            me, status, channel, names = params
            users = names.split()
            chan_obj = self.get_channel(channel) or Channel(self, channel)

            if status == "@":  # Secret channel
                pass
            elif status == "*":  # Private channel
                pass

            event = irc_events.NAMESReplyEvent(self, chan_obj, status, users)
            self.event_manager.run_callback("IRC/NAMESReply", event)

        elif command == "RPL_ENDOFNAMES":
            # Called when the server's done spamming us with NAMES replies.
            me, channel, message = params
            chan_obj = self.get_channel(channel) or Channel(self, channel)

            event = irc_events.NAMESReplyEndEvent(self, chan_obj, message)
            self.event_manager.run_callback("IRC/EndOfNAMES", event)

        elif command == "ERR_INVITEONLYCHAN":
            channel = params[1]
            self.log.warn(
                "Unable to join %s - Channel is invite-only" % channel)

            event = irc_events.InviteOnlyChannelErrorEvent(self,
                                                           Channel(self,
                                                                   channel))
            self.event_manager.run_callback("IRC/InviteOnlyError", event)

        elif str(command) == "972" or str(command) == "ERR_UNKNOWNCOMMAND":
            self.log.warn("Cannot do command '%s': %s" % (params[1],
                                                          params[2]))
            # Called when some command we attempted can't be done.

            event = irc_events.CannotDoCommandErrorEvent(self, params[1],
                                                         params[2])
            self.event_manager.run_callback("IRC/CannotDoCommand", event)

        elif str(command) == "333":  # Channel creation details
            _, channel, creator, when = params
            self.log.info("%s created by %s (%s)" %
                          (channel, creator,
                           time.strftime(
                               "%a, %d %b %Y %H:%M:%S",
                               time.localtime(
                                   float(when)
                               ))
                           ))
            chan_obj = self.get_channel(channel)
            user_obj = self.get_user(nickname=creator) \
                or User(self, nickname=creator, is_tracked=False)

            event = irc_events.ChannelCreationDetailsEvent(self, chan_obj,
                                                           user_obj, when)
            self.event_manager.run_callback("IRC/ChannelCreationDetails",
                                            event)

        elif str(command) in ["265", "266"]:  # RPL_LOCALUSERS, RPL_GLOBALUSERS
            # Usually printed, these are purely informational
            self.log.info(params[3])

            if str(command) == "265":  # LOCALUSERS
                event = irc_events.LOCALUSERSReplyEvent(self, params[3])
                self.event_manager.run_callback("IRC/LOCALUSERS", event)
            else:
                event = irc_events.GLOBALUSERSReplyEvent(self, params[3])
                self.event_manager.run_callback("IRC/GLOBALUSERS", event)

        elif str(command) == "396":  # VHOST was set
            self.log.info("VHOST set to %s by %s" % (params[1], prefix))

            event = irc_events.VHOSTSetEvent(self, params[1], prefix)
            self.event_manager.run_callback("IRC/VHOSTSet", event)

        elif command == "PONG":
            event = irc_events.PongEvent(self)
            self.event_manager.run_callback("IRC/Pong", event)

        else:
            self.log.debug(
                "Unhandled: %s | %s | %s" % (prefix, command, params))
            event = irc_events.UnhandledMessageEvent(self, prefix, command,
                                                     params)
            self.event_manager.run_callback("IRC/UnhandledMessage", event)

    def send_who(self, mask, operators_only=False):
        query = "WHO %s" % mask
        if operators_only:
            query += " o"
        #TODO: Use rate-limited wrapping function for sending
        self.sendLine(query)

    def _get_user_from_user_string(self, user_string, create_temp=True):
        nick, ident, host = self.utils.split_hostmask(user_string)
        user = self.get_user(nickname=nick, ident=ident, host=host)
        if user is None and create_temp:
            user = User(self, nick, ident, host, is_tracked=False)
        return user

    def get_user(self, *args, **kwargs):
        try:
            return self.get_users(*args, **kwargs)[0]
        except IndexError:
            return None

    def get_users(self, nickname=None, ident=None, host=None, fullname=None,
                  hostmask=None):
        matches = []
        if fullname:
            try:
                nickname, ident, host = self.utils.split_hostmask(fullname)
            except:
                return None
        if ident:
            ident = ident.lower()
        if host:
            host = host.lower()
        for user in self.users:
            if (nickname and
                    not self.utils.compare_nicknames(nickname, user.nickname)):
                continue
            if ident and ident != user.ident.lower():
                continue
            if host and host != user.host.lower():
                continue
            if (hostmask and
                    not self.utils.match_hostmask(user.fullname, hostmask)):
                continue
            matches.append(user)
        return matches

    def get_channel(self, channel):
        channel = self.utils.lowercase_nick_chan(channel)
        try:
            return self.channels[channel]
        except KeyError:
            return None

    def set_channel(self, channel, channel_obj):
        channel = self.utils.lowercase_nick_chan(channel)
        self.channels[channel] = channel_obj

    def del_channel(self, channel):
        if isinstance(channel, Channel):
            channel = channel.name
        channel = self.utils.lowercase_nick_chan(channel)
        del self.channels[channel]

    def self_part_channel(self, channel):
        for user in list(channel.users):
            self.user_channel_part(user, channel)
        self.del_channel(channel)

    def user_join_channel(self, nickname, ident, host, channel):
        user = self.get_user(nickname=nickname, ident=ident, host=host)
        if user is None:
            user = User(self, nickname, ident, host, is_tracked=True)
            self.users.append(user)
        user.add_channel(channel)
        channel.add_user(user)
        # For convenience
        return user

    def channel_modes_response(self, channel, modes):
        self.log.debug("Modes for %s: %s" % (channel, modes))
        pass

    def channel_who_response(self, nickname, ident, host, server, status,
                             gecos, channel):
        """User-tracking related
        :type channel: Channel
        """
        # If the user is not known about, create them.
        user = self.get_user(nickname=nickname, ident=ident, host=host)
        if user is None:
            user = self.user_join_channel(nickname, ident, host, channel)
        if not (channel in user.channels and user in channel.users):
            user.add_channel(channel)
            channel.add_user(user)
        for s in status:
            if s in "HG":
                # Here/Gone
                # TODO: Handle H/G status?
                pass
            elif s == "*":
                user.is_oper = True
            elif s in self.ranks.symbols:
                rank = self.ranks.by_symbol(s)
                user.add_rank_in_channel(channel, rank)
            else:
                # A bunch of ircd-specific stuff can appear here. We have no
                # need for it, but plugins could listen for WHO replies
                # themselves if they really need, or we can add stuff if a
                # proper use/specification is given.
                self.log.debug(
                    "Unexpected status in WHO response for user %s: %s" %
                    (user, s))
        user.realname = gecos.split(" ")[-1]

    def user_channel_part(self, user, channel):
        """User-tracking related
        :type channel: Channel
        """
        if not isinstance(user, User):
            user = self.get_user(nickname=user)
        # Remove user from channel and channel from user
        user.remove_channel(channel)
        channel.remove_user(user)
        # Check if they've gone off our radar
        self.user_check_lost_track(user)

    def user_check_lost_track(self, user):
        """User-tracking related"""
        if len(user.channels) == 0:
            self.log.debug("Lost track of user: %s" % user)
            self.users.remove(user)
            user.is_tracked = False
            # TODO: Throw event: lost track of user

    #######################################################################
    # Following this section are functions that are going to be used by   #
    # the plugins and other parts of the system. For example, sending any #
    # messages, joining channels, and so on.                              #
    #######################################################################

    def send_notice(self, target, message):
        self.send_unicode_line(u"NOTICE %s :%s" % (target, message))
