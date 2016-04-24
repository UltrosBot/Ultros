# coding=utf-8
import random
import time

from kitchen.text.converters import to_bytes, to_unicode
from twisted.internet import reactor
from twisted.words.protocols import irc

from system.constants import __version__
from system.commands.manager import CommandManager
from system.decorators.log import deprecated
from system.enums import CommandState
from system.events import general as general_events
from system.events import irc as irc_events
from system.events.manager import EventManager
from system.logging.logger import getLogger
from system.protocols.generic.protocol import ChannelsProtocol
from system.protocols.irc import constants
from system.protocols.irc.channel import Channel
from system.protocols.irc.rank import Ranks
from system.protocols.irc.user import User
from system.translations import Translations
from utils.irc import IRCUtils
from utils.switch import Switch
_ = Translations().get()


class Protocol(irc.IRCClient, ChannelsProtocol):
    """
    Internet Relay Chat server protocol.

    Class layout:
        - Private send/recv functions
        - IRC message handling
            - Initial connection
            - Personal events (force-joined, kicked)
            - Messages (privmsg, notice)
            - User events (joining/leaving, nick changes)
            - Channel events (modes, topic changes)
            - Lower-level event handling (all JOIN messages)
            - CTCP specific command handlers (ctcpQuery_VERSION)
            - Other command replies (WHOREPLY, ISUPPORT)
        - User/Channel functions (wrappers/helpers for _users and _channels)
        - User-tracking
        - Public API functions (send_notice, etc)
    """

    # region Init and shutdown

    __version__ = "1.0.0"

    TYPE = "irc"

    factory = None
    config = None
    log = None
    event_manager = None

    networking = {}
    identity = {}

    nickname = ""
    name = "irc"

    control_chars = "."

    invite_join = False

    _channels = {}  # key is lowercase "#channel" - use get/set/del_channel()

    _ctcp_flood_enabled = True
    _ctcp_flood_time = 30
    _ctcp_flood_max_count = 5

    _ctcp_flood_last = 0
    _ctcp_flood_count = 0

    @property
    def num_channels(self):
        return len(self._channels)

    @property
    def fingers(self):
        return self.config.get("fingers", [])

    # TODO: Make users a set()?
    _users = []
    ourselves = None

    ssl = False

    def get_nickname(self):
        if self.ourselves:
            return self.ourselves.nickname
        return self.nickname

    def __init__(self, name, factory, config):
        # TODO: Replace this with a super if we ever fully replace twisted irc
        # - and no longer inherit from it
        ChannelsProtocol.__init__(self, name, factory, config)

        self.log = getLogger(self.name)
        self.log.info(_("Setting up.."))

        try:
            from twisted.internet import ssl
            self.ssl = True
        except ImportError:
            ssl = False
            self.ssl = False
            self.log.exception(_("Unable to import the SSL library. "
                                 "SSL will not be available."))

        self.event_manager = EventManager()
        self.command_manager = CommandManager()
        self.utils = IRCUtils(self.log)
        # Three dicts for easier lookup
        self.ranks = Ranks()
        # Default prefixes in case the server doesn't send us a RPL_ISUPPORT
        self.ranks.add_rank("o", "@", 0)
        self.ranks.add_rank("v", "+", 1)

        self.networking = config["network"]
        self.identity = config["identity"]
        self.control_chars = config["control_chars"]

        if config["rate_limiting"]["enabled"]:
            self.lineRate = config["rate_limiting"]["line_delay"]

        if "ctcp_flood_protection" in config:
            self._ctcp_flood_enabled = config["ctcp_flood_protection"][
                "enabled"]
            self._ctcp_flood_time = config["ctcp_flood_protection"][
                "ctcp_time"]
            self._ctcp_flood_max_count = config["ctcp_flood_protection"][
                "ctcp_count"]
        else:
            self.log.info(_("No ctcp_flood_protection block in config - "
                            "using default values"))

        try:
            if config["network"]["password"]:
                self.password = config["network"]["password"]
        except KeyError:
            self.log.warning(_("Config doesn't contain network/password "
                               "entry"))

        self.nickname = self.identity["nick"]
        self.invite_join = self.config.get("invite_join", False)

    def shutdown(self):
        self.sendLine("QUIT :%s" % _("Protocol shutdown"))
        self.transport.loseConnection()

    def register(self, nickname, hostname='foo', servername='bar'):
        if self.identity["authentication"].lower() == "sasl":
            self.sendLine("CAP REQ :sasl")  # It has to be sent early
        irc.IRCClient.register(self, nickname, hostname, servername)

    # endregion

    # region Private send/recv functions

    #######################################################################
    # These generally shouldn't be used directly. Instead, the public API #
    # functions should be used.                                           #
    #######################################################################

    def sendLine(self, line, output=False):
        """
        Overriding this because fuck Twisted unicode support.
        """
        if output:
            self.log.info(_("SERVER -> %s") % line)

        line = to_bytes(line)  # The magical line

        irc.IRCClient.sendLine(self, line)

    # endregion

    # region Personal events

    #######################################################################
    # User events relating to self, such as being joined to a channel, or #
    # having our nick changed.                                            #
    #######################################################################

    def signedOn(self):
        """
         Called once we've connected and done our handshake with the IRC server
        """

        # Reset users and channels when we connect, in case we still have them
        # from a previous connection.
        self.ourselves = None
        self._users = []
        self._channels = {}

        self.factory.clientConnected()

        def do_sign_on():
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

            perform = self.config.get("perform", [])

            if perform:
                for line in perform:
                    self.sendLine(line.replace("{NICK}", self.get_nickname()),
                                  output=True)

            reactor.callLater(5, do_channel_joins)

        def do_channel_joins():
            for channel in self.config["channels"]:
                self.join_channel(channel["name"], channel["key"])

            _event = general_events.PostSetupEvent(self, self.config)
            self.event_manager.run_callback("PostSetup", _event)

        self.log.debug(
            _("Scheduling Deferreds for signing on and joining channels"))

        reactor.callLater(5, do_sign_on)

        event = general_events.PreSetupEvent(self, self.config)
        self.event_manager.run_callback("PreSetup", event)

    def joined(self, channel):
        """ Called when we join a channel. """
        self.log.info(_("Joined channel: %s") % channel)
        chan_obj = Channel(self, channel)
        # Do user-tracking in irc_JOIN

        event = irc_events.ChannelJoinedEvent(self, chan_obj)
        self.event_manager.run_callback("IRC/ChannelJoined", event)

    def left(self, channel):
        """ Called when we part a channel.
        This could include opers using /sapart. """
        self.log.info(_("Parted channel: %s") % channel)
        chan_obj = self.get_channel(channel)
        # User-tracking stuff:
        self.self_part_channel(chan_obj)

        event = irc_events.ChannelPartedEvent(self, chan_obj)
        self.event_manager.run_callback("IRC/ChannelParted", event)

    def kickedFrom(self, channel, kicker, message):
        """ Called when we get kicked from a channel. """
        self.log.info(_("Kicked from %s by %s: %s")
                      % (channel, kicker, message))

        user_obj = self.get_user(nickname=kicker)
        channel_obj = self.get_channel(channel)
        # User-tracking stuff:
        self.self_part_channel(channel_obj)

        event = irc_events.KickedEvent(self, channel_obj, user_obj, message)
        self.event_manager.run_callback("IRC/SelfKicked", event)

        password = None

        if channel in self.config["channels"]:
            password = self.config["channels"][channel]["key"]

        if self.config["kick_rejoin"]:
            self.log.info(_("Rejoining in %s seconds..") %
                          self.config["rejoin_delay"])
            reactor.callLater(self.config["rejoin_delay"], self.join_channel,
                              channel, password)
        elif channel in self.config["channels"]:
            if self.config["channels"][channel].get("kick_rejoin", False):
                self.log.info(_("Rejoining in %s seconds..") %
                              self.config["rejoin_delay"])
                reactor.callLater(self.config["rejoin_delay"],
                                  self.join_channel,
                                  channel, password)

    def nickChanged(self, nick):
        """ Called when our nick is forcibly changed. """
        self.log.info(_("Nick changed to %s") % nick)

        event = general_events.NameChangedSelf(self, nick)
        self.event_manager.run_callback("NameChangedSelf", event)

    # endregion

    # region Message events

    def privmsg(self, user, channel, message):
        """ Called when we receive a message - channel or private. """

        try:
            user_obj = self._get_user_from_user_string(user)
        except Exception:
            # Privmsg from the server itself and things (if that happens)
            self.log.trace(_("Message from irregular user: %s") % user)
            user_obj = User(self, nickname=user)

        if self.utils.compare_nicknames(channel, self.get_nickname()):
            channel_obj = user_obj
        else:
            channel_obj = self.get_channel(channel)

        event = general_events.PreMessageReceived(
            self, user_obj, channel_obj, message, "message"
        )

        self.event_manager.run_callback("PreMessageReceived", event)

        if event.printable:
            self.log.info("<%s:%s> %s" % (user_obj.nickname, channel,
                                          event.message))

        if not event.cancelled:
            result = self.command_manager.process_input(
                event.message, user_obj, channel_obj, self,
                self.control_chars, self.get_nickname()
            )

            for case, default in Switch(result[0]):
                if case(CommandState.RateLimited):
                    self.log.debug("Command rate-limited")
                    user_obj.respond("That command has been rate-limited,"
                                     " please try again later.")
                    return  # It was a command
                if case(CommandState.NotACommand):
                    self.log.debug("Not a command")
                    break
                if case(CommandState.UnknownOverridden):
                    self.log.debug("Unknown command overridden")
                    return  # It was a command
                if case(CommandState.Unknown):
                    self.log.debug("Unknown command")
                    break
                if case(CommandState.Success):
                    self.log.debug("Command ran successfully")
                    return  # It was a command
                if case(CommandState.NoPermission):
                    self.log.debug("No permission to run command")
                    return  # It was a command
                if case(CommandState.Error):
                    user_obj.respond("Error running command: %s" % result[1])
                    return  # It was a command
                if default:
                    self.log.debug("Unknown command state: %s" % result[0])
                    break

            second_event = general_events.MessageReceived(
                self, user_obj, channel_obj, event.message, "message"
            )
            self.event_manager.run_callback(
                "MessageReceived", second_event
            )

    def noticed(self, user, channel, message):
        """ Called when we receive a notice - channel or private. """

        try:
            user_obj = self._get_user_from_user_string(user)
        except Exception:
            # Notices from the server itself and things
            self.log.trace(_("Notice from irregular user: %s") % user)
            user_obj = User(self, nickname=user, is_tracked=False)

        if self.utils.compare_nicknames(channel, self.get_nickname()):
            channel_obj = user_obj
        else:
            channel_obj = self.get_channel(channel)

        event = general_events.PreMessageReceived(self,
                                                  user_obj,
                                                  channel_obj,
                                                  message,
                                                  "notice",
                                                  printable=True)
        self.event_manager.run_callback("PreMessageReceived", event)
        if event.printable:
            self.log.info("-%s:%s- %s" % (user, channel, event.message))

        second_event = general_events.MessageReceived(self,
                                                      user_obj,
                                                      channel_obj,
                                                      event.message,
                                                      "notice")
        self.event_manager.run_callback("MessageReceived", second_event)

    def ctcpQuery(self, user, channel, messages):
        """ Called when someone does a CTCP query - channel or private.
        Needs some param analysis."""

        message = messages[0]
        action, data = message[0].upper(), message[1]

        should_block = False
        if self._ctcp_flood_enabled and action != "ACTION":
            if self._ctcp_flood_last + self._ctcp_flood_time < time.time():
                self.log.debug(
                    _("First CTCP in over %s seconds - resetting counter") %
                    self._ctcp_flood_time
                )
                # First CTCP in a while - reset counter
                self._ctcp_flood_last = time.time()
                self._ctcp_flood_count = 0

            self._ctcp_flood_count += 1

            if self._ctcp_flood_count > self._ctcp_flood_max_count:
                self.log.info(_("Too many CTCPs received - blocking"))
                # Received too many messages - block
                should_block = True
                # Reset timer so we continue blocking until the rate slows down
                self._ctcp_flood_last = time.time()

        try:
            user_obj = self._get_user_from_user_string(user)
        except Exception:
            # CTCP from the server itself and things (if that happens)
            self.log.trace(_("CTCP from irregular user: %s") % user)
            user_obj = User(self, nickname=user, is_tracked=False)

        if self.utils.compare_nicknames(channel, self.get_nickname()):
            channel_obj = user_obj
        else:
            channel_obj = self.get_channel(channel)

        event = irc_events.CTCPQueryEvent(self, user_obj, channel_obj,
                                          action, data)
        if should_block:
            event.cancelled = True
        self.event_manager.run_callback("IRC/CTCPQueryReceived", event)

        if action.upper() == "ACTION":
            self.log.info("* %s:%s %s" % (user_obj, channel_obj, data))

            e = general_events.ActionReceived(
                self, user_obj, channel_obj, data
            )

            e.cancelled = event.cancelled

            self.event_manager.run_callback("ActionReceived", e)
        else:
            self.log.info(u"[{} {}] {}".format(
                user.split("!", 1)[0], message[0], message[1] or ""
            ))

        if not event.cancelled:
            # Call super() to handle specific commands appropriately
            irc.IRCClient.ctcpQuery(self, user, channel, messages)

    # endregion

    # region User events

    #######################################################################
    # Handlers for things such as users joining/parting channels.         #
    #######################################################################

    def userJoined(self, user, channel):
        """ Called when someone else joins a channel we're in. """
        self.log.info(_("%s joined %s") % (user.nickname, channel))
        # Note: User tracking is done in irc_JOIN rather than here

        event = irc_events.UserJoinedEvent(self, channel, user)
        self.event_manager.run_callback("IRC/UserJoined", event)

    def userLeft(self, user, channel):
        """ Called when someone else leaves a channel we're in. """
        self.log.info(_("%s parted %s") % (user, channel))
        chan_obj = self.get_channel(channel)
        user_obj = self.get_user(nickname=user)
        # User-tracking stuff
        self.user_channel_part(user_obj, chan_obj)

        event = irc_events.UserPartedEvent(self, chan_obj, user_obj)
        self.event_manager.run_callback("IRC/UserParted", event)

    def userKicked(self, kickee, channel, kicker, message):
        """ Called when someone else is kicked from a channel we're in. """
        self.log.info(_("%s was kicked from %s by %s: %s") % (
            kickee, channel, kicker, message))
        kickee_obj = self.get_user(nickname=kickee)
        kicker_obj = self.get_user(nickname=kicker)
        channel_obj = self.get_channel(channel)
        # User-tracking stuff
        self.user_channel_part(kickee_obj, channel_obj)

        event = irc_events.UserKickedEvent(self,
                                           channel_obj,
                                           kickee_obj,
                                           kicker_obj,
                                           message)
        self.event_manager.run_callback("IRC/UserKicked", event)

    def irc_QUIT(self, user, params):
        """ Called when someone else quits IRC. """
        quitmessage = params[0]
        self.log.info(_("%s has left IRC: %s") % (user, quitmessage))
        # User-tracking stuff
        user_obj = self.get_user(fullname=user)
        temp_chans = set(user_obj.channels)
        for channel in temp_chans:
            self.user_channel_part(user_obj, channel)

        event = irc_events.UserQuitEvent(self, user_obj, quitmessage)
        self.event_manager.run_callback("IRC/UserQuit", event)

        event = general_events.UserDisconnected(self, user_obj)
        self.event_manager.run_callback("UserDisconnected", event)

    # endregion

    # region Channel events

    #######################################################################
    # Handlers for things such as channel mode changes and topic changes. #
    #######################################################################

    def modeChanged(self, user, channel, action, modes, args):
        """
        Called when someone changes a mode. Action is a bool specifying
        whether the mode was being set or unset.
        If it's a usermode, channel is the user being changed.

        Note: If it's a user-mode, channel_obj is set to None. Eventually, this
        method should be placed elsewhere and call user/channelModeChanged()
        instead.
        """
        self.log.info(_("%s sets mode %s: %s%s %s") % (
            user, channel, "+" if action else "-", modes,
            " ".join([str(x) for x in args if x is not None])
        ))

        # Get user/channel objects
        try:
            user_obj = self._get_user_from_user_string(user)
        except Exception:
            # Mode change from the server itself and things
            self.log.trace(_("Mode change from irregular user: %s") % user)
            user_obj = User(self, nickname=user, is_tracked=False)
            # Note: Unlike in privmsg/notice/ctcpQuery, channel_obj = None when
        # the target is ourself, rather than a user object. Perhaps this should
        # be changed for clarity?
        channel_obj = None
        if not self.utils.compare_nicknames(self.get_nickname(), channel):
            channel_obj = self.get_channel(channel)

        # Handle the mode changes
        for x in xrange(len(modes)):
            if channel_obj is None:
                # User mode (almost definitely always ourselves)
                # TODO: Handle this (usermodes)
                # Unsure how to handle this - is len(args) == len(modes)?
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
                        _("Rank mode %s set on invalid user %s in channel %s")
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

    def topicUpdated(self, user, channel, newTopic):
        """ Called when the topic is updated in a channel -
        also called when we join a channel. """
        self.log.info(
            _("Topic for %s: %s (set by %s)") % (channel, newTopic, user)
        )

        user_obj = self.get_user(nickname=user) or User(self, nickname=user,
                                                        is_tracked=False)
        chan_obj = self.get_channel(channel) or Channel(self, channel)

        event = irc_events.TopicUpdatedEvent(self, chan_obj, user_obj,
                                             newTopic)
        self.event_manager.run_callback("IRC/TopicUpdated", event)

    # endregion

    # region Lower-level event handling

    #######################################################################
    # Lower-level event handling. For example, irc_JOIN is called for     #
    # every JOIN message received, not just ones about other users. These #
    # typically call the ones above, such as joined() and useJoined().    #
    #######################################################################

    def irc_JOIN(self, prefix, params):
        """ Called on any join message
        :param prefix: The user joining
        :param params: The channel(s?) joined
        """
        # irc.IRCClient.irc_JOIN(self, prefix, params)
        # Removed as we can do this better than the library

        # For some reason, userJoined only gives the user's nick, so we do
        # user tracking here

        # There will only ever be one channel, so just get that. No need to
        # iterate.

        channel = params[-1]
        channel_obj = self.get_channel(channel)
        if channel_obj is None:
            channel_obj = Channel(self, channel)
            self.set_channel(channel, channel_obj)

        nickname, ident, host = self.utils.split_hostmask(prefix)
        user_obj = self.user_join_channel(nickname,
                                          ident,
                                          host,
                                          channel_obj)

        if self.utils.compare_nicknames(nickname, self.get_nickname()):
            # User-tracking stuff
            if self.ourselves is None:
                self.ourselves = user_obj
            self.send_who(channel)
            # Call the self-joined-channel method manually, since we're no
            # longer calling the super method.
            self.joined(channel)
        else:
            # Since we're using our own function and the library doesn't
            # actually do anything with this, we can simply supply the
            # user and channel objects.
            self.userJoined(user_obj, channel_obj)

    def irc_NICK(self, prefix, params):
        """ Called when someone changes their nick.
        Surprisingly, twisted doesn't have a handler for this. """

        oldnick = prefix.split("!", 1)[0]
        newnick = params[0]

        user_obj = self.get_user(nickname=oldnick)

        if not user_obj:
            user_obj = User(self, newnick, is_tracked=False)
        user_obj.nickname = newnick

        self.log.info(_("%s is now known as %s") % (oldnick, newnick))

        event = general_events.NameChanged(self, user_obj, oldnick)
        self.event_manager.run_callback("NameChanged", event)

    # endregion

    # region CTCP specific command responses

    #######################################################################
    # Handlers for specific CTCP commands. These are dynamically found  . #
    # and called by ctcpQuery() - simply adding one makes it used.        #
    #######################################################################

    def ctcpQuery_VERSION(self, user, channel, data_):
        user_obj = self._get_user_from_user_string(user, False)
        self.send_ctcp_reply(
            user_obj, "VERSION", "Ultros v{}".format(__version__))

    def ctcpQuery_SOURCE(self, user, channel, data_):
        user_obj = self._get_user_from_user_string(user, False)
        self.send_ctcp_reply(user_obj, "SOURCE", "http://ultros.io")

    def ctcpQuery_FINGER(self, user, channel, data):
        fingers = self.fingers

        if not fingers:
            return

        user_obj = self._get_user_from_user_string(user, False)
        self.send_ctcp_reply(user_obj, "FINGER", random.choice(fingers))

    # endregion

    # region SASL stuff

    def sendSASL(self, name, password):
        sasl = (
            "%s\0%s\0%s" % (name, name, password)
        ).encode("base64").strip()
        self.sendLine("AUTHENTICATE PLAIN")
        self.sendLine("AUTHENTICATE %s" % sasl)

    def irc_CAP(self, prefix, params):
        self.log.debug("Capability message: %s / %s" % (prefix, params))

        if (
            len(params) < 2 or
            params[1] != "ACK" or
            params[2].split() != ["sasl"]
        ):  # PEP8!
            if self.identity["authentication"].lower() == "sasl":
                self.log.error(
                    "SASL auth requested, but the server doesn't support "
                    "it!"
                )
                self.log.error(
                    "The bot will not login. Please correct this."
                )
        else:
            if self.identity["authentication"].lower() == "sasl":
                self.sendSASL(
                    self.identity["auth_name"], self.identity["auth_pass"]
                )

    def irc_900(self, prefix, params):
        # "You are now logged in as x"
        self.log.debug("IRC 900")
        if len(params) > 3:
            self.log.info(params[3])

    def irc_903(self, prefix, params):
        self.log.debug("IRC 903")
        self.log.info(params[1])
        self.sendLine("CAP END")

    def irc_904(self, prefix, params):
        self.log.debug("IRC 904")
        self.log.warn(params[1])

    def irc_905(self, prefix, params):
        self.log.debug("IRC 905")
        self.log.warn(params[1])

    # endregion

    # region Other RPL_* handlers

    def irc_RPL_WHOREPLY(self, *nargs):
        """ Called when we get a WHO reply from the server.
        I'm seriously wondering if we even need this. """
        data_ = nargs[1]

        try:
            channel = data_[1]
            ident = data_[2]  # Starts with a ~ if there's no identd present
            host = data_[3]
            server = data_[4]
            nick = data_[5]
            status = data_[6]  # .strip("G").strip("H").strip("*")
            gecos = data_[7]  # Hops, realname
        except Exception:
            self.log.exception("Unable to parse WHO reply")
            return

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
            data_ = {"ident": ident, "host": host, "server": server,
                     "status": status, "gecos": gecos}

            event = irc_events.WHOReplyEvent(self, chan_obj, user_obj, data_)
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
            self.log.trace(_("RPL_ISUPPORT received: %s") % param)
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
            elif prm == "CHANTYPES":
                derp = self.supported.getFeature("CHANTYPES")
                self.utils.chan_types =\
                    self.supported.getFeature("CHANTYPES")[0]  # Tuple

        event = irc_events.ISUPPORTReplyEvent(self, prefix, params)
        self.event_manager.run_callback("IRC/ISUPPORT", event)

    def receivedMOTD(self, motd):
        """ Called when we receive the MOTD. """
        self.log.info(_(" ===   MOTD   === "))
        for line in motd:
            self.log.info(line)
        self.log.info(_(" === END MOTD ==="))

        event = irc_events.MOTDReceivedEvent(self, motd)
        self.event_manager.run_callback("IRC/MOTDReceived", event, True)

    def irc_unknown(self, prefix, command, params):
        """ Packets that aren't handled elsewhere get passed to this function.
        """

        if command == "RPL_BANLIST":
            # This is a single entry in a channel's ban list.
            ___, channel, mask, owner, btime = params
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
                _("Unable to join %s - Channel is invite-only") % channel)

            event = irc_events.InviteOnlyChannelErrorEvent(self,
                                                           Channel(self,
                                                                   channel))
            self.event_manager.run_callback("IRC/InviteOnlyError", event)

        elif command == "ERR_ALREADYREGISTRED":
            message = params[1]
            self.log.warn("Already registered: %s" % message)

        elif str(command) == "972" or str(command) == "ERR_UNKNOWNCOMMAND":
            self.log.warn(_("Cannot do command '%s': %s") % (params[1],
                                                             params[2]))
            # Called when some command we attempted can't be done.

            event = irc_events.CannotDoCommandErrorEvent(self, params[1],
                                                         params[2])
            self.event_manager.run_callback("IRC/CannotDoCommand", event)

        elif str(command) == "333":  # Channel creation details
            ___, channel, creator, when = params
            self.log.info(_("%s created by %s (%s)") %
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
            if len(params) > 3:
                data = params[3]
            else:
                data = params[1]

            self.log.info(data)

            if str(command) == "265":  # LOCALUSERS
                event = irc_events.LOCALUSERSReplyEvent(self, data)
                self.event_manager.run_callback("IRC/LOCALUSERS", event)
            else:
                event = irc_events.GLOBALUSERSReplyEvent(self, data)
                self.event_manager.run_callback("IRC/GLOBALUSERS", event)

        elif str(command) == "396":  # VHOST was set
            self.log.info(_("VHOST set to %s by %s") % (params[1], prefix))

            event = irc_events.VHOSTSetEvent(self, params[1], prefix)
            self.event_manager.run_callback("IRC/VHOSTSet", event)

        elif command == "PONG":
            event = irc_events.PongEvent(self)
            self.event_manager.run_callback("IRC/Pong", event)

        elif command == "INVITE":
            mask = self.utils.split_hostmask(prefix)
            user = self.get_user(*mask)
            if not user:
                user = User(self, *mask, is_tracked=False)
            channel = params[1]

            self.log.info(_("Invited to %s by %s.") % (channel, user.nickname))

            event = irc_events.InvitedEvent(self, user, channel,
                                            self.invite_join)
            self.event_manager.run_callback("IRC/Invited", event)
            if self.invite_join:
                self.log.info(_("Automatically joining %s..") % channel)
                self.join_channel(params[1])

        else:
            self.log.debug(
                "Unhandled: %s | %s | %s" % (prefix, command, params))
            event = irc_events.UnhandledMessageEvent(self, prefix, command,
                                                     params)
            self.event_manager.run_callback("IRC/UnhandledMessage", event)

    # endregion

    # region User/Channel functions

    #######################################################################
    # Functions for interacting with self._users and self._channels. Use  #
    # these instead of accessing them directly.                           #
    #######################################################################

    def get_extra_groups(self, user, target=None):
        if target:
            if isinstance(user, basestring):
                user = self.get_user(user)
            if not user:
                return []

            rank = user.get_highest_rank_in_channel(target)

            if not rank:
                return []

            self.log.debug("Rank for {}: {}".format(user, rank))
            return ["{}-{}".format(self.TYPE, rank.symbol)]

        return []

    def _get_user_from_user_string(self, user_string, create_temp=True):
        nick, ident, host = self.utils.split_hostmask(user_string)
        user = self.get_user(nickname=nick, ident=ident, host=host)
        if user is None and create_temp:
            user = User(self, nick, ident, host, is_tracked=False)
        return user

    def get_user(self, *args, **kwargs):
        # self.log.debug("Searching for user | %s | %s" % (args, kwargs))
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
            except Exception:
                return None
        if ident:
            ident = ident.lower()
        if host:
            host = host.lower()
        for user in self._users:
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
            return self._channels[channel]
        except KeyError:
            return None

    def set_channel(self, channel, channel_obj):
        channel = self.utils.lowercase_nick_chan(channel)
        self._channels[channel] = channel_obj

    def del_channel(self, channel):
        if isinstance(channel, Channel):
            channel = channel.name
        channel = self.utils.lowercase_nick_chan(channel)
        del self._channels[channel]

    def self_part_channel(self, channel):
        for user in list(channel.users):
            self.user_channel_part(user, channel)
        self.del_channel(channel)

    # endregion

    # region User-tracking

    def user_join_channel(self, nickname, ident, host, channel):
        user = self.get_user(nickname=nickname, ident=ident, host=host)
        if user is None:
            user = User(self, nickname, ident, host, is_tracked=True)
            self._users.append(user)
        user.add_channel(channel)
        channel.add_user(user)
        # For convenience
        return user

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
            if s == "H":  # Here
                user.set_away(False)
            elif s == "G":  # Gone
                # TODO: Away message?
                user.set_away(True)
            elif s == "*":
                user.is_oper = True
            elif s in self.ranks.symbols:
                rank = self.ranks.by_symbol(s)
                user.add_rank_in_channel(channel, rank)
            else:
                # A bunch of IRCd-specific stuff can appear here. We have no
                # need for it, but plugins could listen for WHO replies
                # themselves if they really need, or we can add stuff if a
                # proper use/specification is given.
                self.log.debug(
                    _("Unexpected status in WHO response for user %s: %s") %
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
            self.log.trace(_("Lost track of user: %s") % user)
            self._users.remove(user)
            user.is_tracked = False
            # TODO: Throw event: lost track of user
            # Do we really need an event for this?

    # endregion

    # region Public API functions

    #######################################################################
    # Functions to be used by plugins and other parts of the system. For  #
    # example, sending any messages, joining channels, and so on.         #
    # Note: Some other public functions aren't here as they fit into      #
    # other sections. These include:                                      #
    #   - get_channel()                                                   #
    #   - get_user() and get_users()                                      #
    #######################################################################

    def send_msg(self, target, message, target_type=None, use_event=True):
        if isinstance(target, str):
            if self.utils.is_channel(target):
                # Channel
                target = self.get_channel(target)
                if not target:
                    return False
            else:
                target = self.get_user(target)
                if not target:
                    target = User(self, target)

        if isinstance(target, User):
            self.send_notice(target, message, use_event)
        elif isinstance(target, Channel):
            self.send_privmsg(target, message, use_event)
        else:
            return False
        return True

    def send_action(self, target, message, target_type=None, use_event=True):
        if isinstance(target, str):
            if self.utils.is_channel(target):
                # Channel
                target = self.get_channel(target)
                if not target:
                    return False
            else:
                target = self.get_user(target)
                if not target:
                    target = User(self, target)

        if isinstance(target, Channel) or isinstance(target, User):
            event = general_events.ActionSent(self, target, message)
            self.event_manager.run_callback("ActionSent", event)

            if not event.cancelled:
                for line in message.split("\n"):
                    self.send_ctcp(target, "ACTION", line)
                return True
            return False
        return False

    def send_raw(self, message):
        if "\n" in message:
            messages = message.replace("\r", "").split("\n")
        else:
            messages = [message]

        for line in messages:
            self.sendLine(line, True)

    @deprecated("Use join_channel()")
    def join(self, channel, key=None):
        """
        DEPRECATED: Use join_channel
        """
        # NOTE: This method is only here to prevent unwanted behaviour from
        # anything calling the base twisted irc client method. It should be
        # removed if we ever get around to removing that dependency.
        self.join_channel(channel, key)

    @deprecated("Use leave_channel()")
    def leave(self, *args, **kwargs):
        """
        DEPRECATED: Use leave_channel()
        """
        # NOTE: This method is only here to prevent unwanted behaviour from
        # anything calling the base twisted irc client method. It should be
        # removed if we ever get around to removing that dependency.
        self.leave_channel(*args, **kwargs)

    part = leave

    def invite(self, user, channel):
        """
        Attempt to invite user to channel

        @type user: C{str}
        @param user: The user to invite
        @type channel: C{str}
        @param channel: The channel to invite the user too

        @since: 11.0
        """
        self.sendLine(u"INVITE %s %s" % (user, channel))

    def topic(self, channel, topic=None):
        """
        Attempt to set the topic of the given channel, or ask what it is.

        If topic is None, then I sent a topic query instead of trying to set
        the topic. The server should respond with a TOPIC message containing
        the current topic of the given channel.

        @type channel: C{str}
        @param channel: The name of the channel to change the topic on.
        @type topic: C{str}
        @param topic: If specified, what to set the topic to.
        """
        # << TOPIC #xtestx :fff
        if topic is None:
            self.sendLine(u"TOPIC %s" % channel)
        else:
            self.sendLine(u"TOPIC %s :%s" % (channel, topic))

    @deprecated("Use send_msg()")
    def say(self, channel, message, length=None):
        """
        DEPRECATED: Use send_msg

        The length parameter is ignored.
        """
        # NOTE: This method is only here to prevent unwanted behaviour from
        # anything calling the base twisted irc client method. It should be
        # removed if we ever get around to removing that dependency.
        self.send_msg(channel, message)

    def channel_ban(self, user, channel=None, reason=None, force=False):
        # TODO: Event?
        # TODO: Ban types
        if not force:
            if not self.ourselves.can_kick(user, channel):
                self.log.trace("Tried to ban, but don't have permission")
                return False
        if isinstance(user, str):
            user = self.get_user(user)
        if channel is None:
            return False
        self.sendLine(u"MODE %s +b *!*@%s" % (channel, user.host))
        self.channel_kick(user, channel, reason, force)
        return True

    def channel_kick(self, user, channel=None, reason=None, force=False):
        # TODO: Event?
        if not force:
            if not self.ourselves.can_kick(user, channel):
                self.log.trace("Tried to kick, but don't have permission")
                return False
        if isinstance(user, str):
            user = self.get_user(user)
        if channel is None:
            return False
        if reason:
            self.sendLine(u"KICK %s %s :%s" % (channel, user, reason))
        else:
            self.sendLine(u"KICK %s %s" % (channel, user))
        return True

    def global_ban(self, user, reason=None, force=False, duration="1d"):
        if reason is None:
            reason = "Automated ban"

        if force or self.ourselves.is_oper:
            # TODO: Event?
            # TODO: Ban types
            self.sendLine(u"GLINE *@{} {} :{}".format(
                user.host, duration, reason
            ))
            return True
        return False

    def global_kick(self, user, reason=None, force=False):
        if force or self.ourselves.is_oper:
            # TODO: Event?
            if reason:
                self.sendLine(u"KILL {}".format(user))
            else:
                self.sendLine(u"KILL {} {}".format(user, reason))
            return True
        return False

    def join_channel(self, channel, password=None):
        if password:
            self.sendLine(u"JOIN %s %s" % (channel, password))
        else:
            self.sendLine(u"JOIN %s" % (channel,))
        return True

    def leave_channel(self, channel, reason=None):
        if reason:
            self.sendLine(u"PART %s :%s" % (channel, reason))
        else:
            self.sendLine(u"PART %s" % (channel,))
        return True

    def send_notice(self, target, message, use_event=True):
        if not message:
            message = " "
        msg = to_unicode(message)
        if use_event:
            event = general_events.MessageSent(self, "notice", target,
                                               msg)
            self.event_manager.run_callback("MessageSent", event)
            msg = to_unicode(event.message)

            if event.printable:
                self.log.info("-> -%s- %s" % (target, msg))
        else:
            self.log.info("-> -%s- %s" % (target, msg))

        if isinstance(target, User):
            target = to_unicode(target.nickname)
        elif isinstance(target, Channel):
            target = to_unicode(target.name)

        for line in msg.split("\n"):
            self.sendLine(u"NOTICE %s :%s" % (target, line))

    def send_notice_no_event(self, target, message):
        """
        Sends a notice without printing it or firing an event.
        """
        if not message:
            message = " "
        if isinstance(target, User):
            target = to_unicode(target.nickname)
        elif isinstance(target, Channel):
            target = to_unicode(target.name)
        msg = to_unicode(message)

        for line in msg.split("\n"):
            self.sendLine(u"NOTICE %s :%s" % (target, line))

    def send_privmsg(self, target, message, use_event=True):
        if not message:
            message = " "
        msg = to_unicode(message)
        if use_event:
            event = general_events.MessageSent(self, "message", target,
                                               msg)
            self.event_manager.run_callback("MessageSent", event)
            msg = to_unicode(event.message)

            if event.printable:
                self.log.info("-> *%s* %s" % (target, msg))
        else:
            self.log.info("-> *%s* %s" % (target, msg))

        if isinstance(target, User):
            target = to_unicode(target.nickname)
        elif isinstance(target, Channel):
            target = to_unicode(target.name)

        for line in msg.split("\n"):
            self.sendLine(u"PRIVMSG %s :%s" % (target, line))

    def send_privmsg_no_event(self, target, message):
        """
        Sends a privmsg without printing it or firing an event.
        """
        if not message:
            message = " "
        if isinstance(target, User):
            target = to_unicode(target.nickname)
        elif isinstance(target, Channel):
            target = to_unicode(target.name)
        msg = to_unicode(message)

        for line in msg.split("\n"):
            self.sendLine(u"PRIVMSG %s :%s" % (target, line))

    def send_ctcp(self, target, command, args=None):
        if isinstance(target, User):
            target = to_unicode(target.nickname)
        elif isinstance(target, Channel):
            target = to_unicode(target.name)
        command = to_unicode(command)
        message = command
        if args and len(args):
            message = u"%s %s" % (command, args)
        self.send_privmsg_no_event(target, constants.CTCP + message +
                                   constants.CTCP)

    def send_ctcp_reply(self, target, command, args=None):
        if isinstance(target, User):
            target = to_unicode(target.nickname)
        elif isinstance(target, Channel):
            target = to_unicode(target.name)
        command = to_unicode(command)
        message = command
        if args and len(args):
            message = u"%s %s" % (command, args)
        self.send_notice_no_event(target, constants.CTCP + message +
                                  constants.CTCP)

    def send_who(self, mask, operators_only=False):
        query = u"WHO %s" % mask
        if operators_only:
            query += " o"
        self.sendLine(query)

    # endregion
    pass  # To make the last region work in PyCharm
