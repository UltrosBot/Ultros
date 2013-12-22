#!/usr/bin/env python
# coding=utf-8

__author__ = 'Gareth Coles'

# This is a modified version of Chaosteil's open-domain Mumble library.
# The original code can be found on GitHub, at the following link..
# https://github.com/Chaosteil/rdiablo-mumble-bot/blob/master/
# File: mumble_protocol.py


import cgi
import logging
import platform
import re
import struct

from twisted.internet import reactor, ssl

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.events import general as general_events
from system.events import mumble as mumble_events
from system.protocols.generic.protocol import Protocol as GenericProtocol
from system.protocols.mumble import Mumble_pb2
from system.protocols.mumble.user import User
from system.protocols.mumble.channel import Channel

from utils.html import html_to_text
from utils.log import getLogger
from utils.misc import output_exception

log = logging.getLogger(__name__)


class Protocol(GenericProtocol):
    VERSION_MAJOR = 1
    VERSION_MINOR = 2
    VERSION_PATCH = 4

    VERSION_DATA = (VERSION_MAJOR << 16)\
        | (VERSION_MINOR << 8) \
        | VERSION_PATCH

    # From the Mumble protocol documentation
    PREFIX_FORMAT = ">HI"
    PREFIX_LENGTH = 6

    # This specific order of IDs is extracted from
    # https://github.com/mumble-voip/mumble/blob/master/src/Message.h
    ID_MESSAGE = [
        Mumble_pb2.Version,
        Mumble_pb2.UDPTunnel,
        Mumble_pb2.Authenticate,
        Mumble_pb2.Ping,
        Mumble_pb2.Reject,
        Mumble_pb2.ServerSync,
        Mumble_pb2.ChannelRemove,
        Mumble_pb2.ChannelState,
        Mumble_pb2.UserRemove,
        Mumble_pb2.UserState,
        Mumble_pb2.BanList,
        Mumble_pb2.TextMessage,
        Mumble_pb2.PermissionDenied,
        Mumble_pb2.ACL,
        Mumble_pb2.QueryUsers,
        Mumble_pb2.CryptSetup,
        Mumble_pb2.ContextActionModify,
        Mumble_pb2.ContextAction,
        Mumble_pb2.UserList,
        Mumble_pb2.VoiceTarget,
        Mumble_pb2.PermissionQuery,
        Mumble_pb2.CodecVersion,
        Mumble_pb2.UserStats,
        Mumble_pb2.RequestBlob,
        Mumble_pb2.ServerConfig
    ]

    # Reversing the IDs, so we are able to backreference.
    MESSAGE_ID = dict([(v, k) for k, v in enumerate(ID_MESSAGE)])

    PING_REPEAT_TIME = 5

    channels = {}
    users = {}

    pinging = True
    name = "mumble"

    def __init__(self, factory, config):
        self.received = ""
        self.factory = factory
        self.config = config
        self.log = getLogger("Mumble")
        self.log.info("Setting up..")

        self.command_manager = CommandManager.instance()
        self.event_manager = EventManager.instance()

        self.username = config["identity"]["username"]
        self.password = config["identity"]["password"]
        self.networking = config["network"]
        self.tokens = config["identity"]["tokens"]

        self.control_chars = config["control_chars"]

        event = general_events.PreConnectEvent(self, config)
        self.event_manager.run_callback("PreConnect", event)

        reactor.connectSSL(
            self.networking["address"],
            self.networking["port"],
            self.factory,
            ssl.ClientContextFactory(),
            120
        )

        event = general_events.PostConnectEvent(self, config)
        self.event_manager.run_callback("PostConnect", event)

    def shutdown(self):
        self.msg("Disconnecting: Protocol shutdown")
        self.transport.loseConnection()

    def connectionMade(self):
        self.log.info("Connected to server.")

        # In the mumble protocol you must first send your current version
        # and immediately after that the authentication data.
        #
        # The mumble server will respond with a version message right after
        # this one.
        version = Mumble_pb2.Version()

        version.version = Protocol.VERSION_DATA
        version.release = "%d.%d.%d" % (Protocol.VERSION_MAJOR,
                                        Protocol.VERSION_MINOR,
                                        Protocol.VERSION_PATCH)
        version.os = platform.system()
        version.os_version = "Mumble %s Twisted Protocol" % version.release

        # Here we authenticate
        auth = Mumble_pb2.Authenticate()
        auth.username = self.username
        if self.password:
            auth.password = self.password
        for token in self.tokens:
            auth.tokens.append(token)

        # And now we send both packets one after another
        self.sendProtobuf(version)
        self.sendProtobuf(auth)

        event = general_events.PreSetupEvent(self, self.config)
        self.event_manager.run_callback("PreSetup", event)

        # Then we initialize our ping handler
        self.init_ping()

        # Then we mute ourselves to prevent errors with voice packets
        message = Mumble_pb2.UserState()
        message.self_mute = True
        message.self_deaf = True

        self.sendProtobuf(message)

    def dataReceived(self, recv):
        # Append our received data
        self.received = self.received + recv

        # If we have enough bytes to read the header, we do that
        while len(self.received) >= Protocol.PREFIX_LENGTH:
            msg_type, length = \
                struct.unpack(Protocol.PREFIX_FORMAT,
                              self.received[:Protocol.PREFIX_LENGTH])

            full_length = Protocol.PREFIX_LENGTH + length

            #self.log.debug("Length: %d" % length)
            #self.log.debug("Message type: %d" % msg_type)

            # Check if this this a valid message ID
            if msg_type not in Protocol.MESSAGE_ID.values():
                self.log.error('Message ID not available.')
                self.transport.loseConnection()
                return

            # We need to check if we have enough bytes to fully read the
            # message
            if len(self.received) < full_length:
                self.log.debug("Need to fill data")
                return

            # Read the specific message
            msg = Protocol.ID_MESSAGE[msg_type]()
            msg.ParseFromString(
                self.received[Protocol.PREFIX_LENGTH:
                              Protocol.PREFIX_LENGTH + length])

            # Handle the message
            try:
                self.recvProtobuf(msg_type, msg)
            except Exception as e:
                self.log.error("Exception while handling data.")
                output_exception(self.log, logging.ERROR)

            self.received = self.received[full_length:]

    def sendProtobuf(self, message):
        # We find the message ID
        msg_type = Protocol.MESSAGE_ID[message.__class__]
        # Serialize the message
        msg_data = message.SerializeToString()
        length = len(msg_data)

        # Compile the data with the header
        data = struct.pack(Protocol.PREFIX_FORMAT, msg_type, length) + msg_data

        # Send the data
        self.transport.write(data)

    def recvProtobuf(self, msg_type, message):
        if isinstance(message, Mumble_pb2.Version):
            # version, release, os, os_version
            self.log.info("Connected to Murmur v%s" % message.release)
            event = general_events.PostSetupEvent(self, self.config)
            self.event_manager.run_callback("PostSetup", event)
        elif isinstance(message, Mumble_pb2.Reject):
            # version, release, os, os_version
            self.log.info("Could not connect to server: %s - %s" %
                          (message.type, message.reason))

            self.transport.loseConnection()
            self.pinging = False
        elif isinstance(message, Mumble_pb2.CodecVersion):
            # alpha, beta, prefer_alpha, opus
            alpha = message.alpha
            beta = message.beta
            prefer_alpha = message.prefer_alpha
            opus = message.opus

            event = mumble_events.CodecVersion(self, alpha, beta, prefer_alpha,
                                               opus)
            self.event_manager.run_callback("Mumble/CodecVersion", event)
        elif isinstance(message, Mumble_pb2.CryptSetup):
            # key, client_nonce, server_nonce
            key = message.key
            c_n = message.client_nonce
            s_n = message.server_nonce

            event = mumble_events.CryptoSetup(self, key, c_n, s_n)
            self.event_manager.run_callback("Mumble/CryptoSetup", event)
        elif isinstance(message, Mumble_pb2.ChannelState):
            # channel_id, name, position, [parent]
            self.handle_msg_channelstate(message)
        elif isinstance(message, Mumble_pb2.PermissionQuery):
            # channel_id, permissions, flush
            channel = self.channels[message.channel_id]
            permissions = message.permissions
            flush = message.flush
            event = mumble_events.PermissionsQuery(self, channel, permissions,
                                                   flush)
            self.event_manager.run_callback("Mumble/PermissionsQuery", event)
        elif isinstance(message, Mumble_pb2.UserState):
            # session, name,
            # [user_id, suppress, hash, actor, self_mute, self_deaf]
            self.handle_msg_userstate(message)
        elif isinstance(message, Mumble_pb2.ServerSync):
            # session, max_bandwidth, welcome_text, permissions
            session = message.session
            max_bandwidth = message.max_bandwidth
            permissions = message.permissions
            welcome_text = html_to_text(message.welcome_text, True)
            self.log.info("===   Welcome message   ===")
            for line in welcome_text.split("\n"):
                self.log.info(line)
            self.log.info("=== End welcome message ===")

            event = mumble_events.ServerSync(self, session, max_bandwidth,
                                             welcome_text, permissions)
            self.event_manager.run_callback("Mumble/ServerSync", event)
        elif isinstance(message, Mumble_pb2.ServerConfig):
            # max_bandwidth, welcome_text, allow_html, message_length,
            # image_message_length
            max_bandwidth = message.max_bandwidth
            welcome_text = message.welcome_text
            self.allow_html = message.allow_html
            message_lenth = message.message_length
            image_message_length = message.image_message_length

            event = mumble_events.ServerConfig(self, max_bandwidth,
                                               welcome_text, self.allow_html,
                                               message_lenth,
                                               image_message_length)
            self.event_manager.run_callback("Mumble/ServerConfig", event)
        elif isinstance(message, Mumble_pb2.Ping):
            # timestamp, good, late, lost, resync, udp_packets, tcp_packets,
            # udp_ping_avg, udp_ping_var, tcp_ping_avg, tcp_ping_var
            timestamp = message.timestamp
            good = message.good
            late = message.late
            lost = message.lost
            resync = message.resync
            udp = message.udp_packets
            tcp = message.tcp_packets
            udp_a = message.udp_ping_avg
            udp_v = message.udp_ping_var
            tcp_a = message.tcp_ping_avg
            tcp_v = message.tcp_ping_var

            event = mumble_events.Ping(self, timestamp, good, late, lost,
                                       resync, tcp, udp, tcp_a, udp_a, tcp_v,
                                       udp_v)

            self.event_manager.run_callback("Mumble/Ping", event)
        elif isinstance(message, Mumble_pb2.UserRemove):
            # session, actor, reason, ban
            session = message.session
            actor = message.actor
            reason = message.reason
            ban = message.ban

            if message.session in self.users:
                user = self.users[message.session]
                self.log.info("User left: %s" %
                              user)
                user.channel.remove_user(user)
                del self.users[message.session]
            else:
                user = None

            event = mumble_events.UserRemove(self, session, actor, user,
                                             reason, ban)
            self.event_manager.run_callback("Mumble/UserRemove", event)

            s_event = general_events.UserDisconnected(self, user)
            self.event_manager.run_callback("UserDisconnected", s_event)
        elif isinstance(message, Mumble_pb2.TextMessage):
            # actor, channel_id, message
            self.handle_msg_textmessage(message)
        else:
            self.log.debug("Unknown message type: %s" % message.__class__)
            self.log.debug("Received message '%s' (%d):\n%s"
                           % (message.__class__, msg_type, str(message)))

            event = mumble_events.Unknown(self, type(message), message)
            self.event_manager.run_callback("Mumble/Unknown", event)

    def init_ping(self):
        # Call ping every PING_REPEAT_TIME seconds.
        reactor.callLater(Protocol.PING_REPEAT_TIME, self.ping_handler)

    def ping_handler(self):
        if not self.pinging:
            return
        self.log.debug("Sending ping")

        # Ping has only optional data, no required
        ping = Mumble_pb2.Ping()
        self.sendProtobuf(ping)

        self.init_ping()

    def handle_msg_channelstate(self, message):
        if not message.channel_id in self.channels:
            parent = None
            if message.HasField('parent'):
                parent = message.parent
            links = []
            if message.links:
                links = list(message.links)
                for link in links:
                    self.log.debug("Channel link: %s to %s" %
                                   (self.channels[link],
                                    self.channels[message.channel_id]))
            self.channels[message.channel_id] = Channel(self,
                                                        message.channel_id,
                                                        message.name,
                                                        parent,
                                                        message.position,
                                                        links)
            self.log.info("New channel: %s" % message.name)
        if message.links_add:
            for link in message.links_add:
                self.channels[message.channel_id].add_link(link)
                self.log.info("Channel link added: %s to %s" %
                              (self.channels[link],
                               self.channels[message.channel_id]))
                event = mumble_events.ChannelLinked(self, self.channels[link],
                                                    self.channels
                                                    [message.channel_id])
                                                    # TOTALLY MORE READABLE
                                                    # GOOD JOB PEP8
                self.event_manager.run_callback("Mumble/ChannelLinked", event)
        if message.links_remove:
            for link in message.links_remove:
                self.channels[message.channel_id].remove_link(link)
                self.log.info("Channel link removed: %s from %s" %
                              (self.channels[link],
                               self.channels[message.channel_id]))
                event = mumble_events.ChannelUnlinked(self, self.channels
                                                      [link], self.channels
                                                      [message.channel_id])
                                                      # Jesus fuck.
                self.event_manager.run_callback("Mumble/ChannelUnlinked",
                                                event)

    def handle_msg_userstate(self, message):
        if message.name and message.session not in self.users:
            # Note: I'm not sure if message.name should ever be empty and
            # not in self.users - rakiru
            self.users[message.session] = User(self,
                                               message.session,
                                               message.name,
                                               self.channels[
                                                   message.channel_id],
                                               message.mute,
                                               message.deaf,
                                               message.suppress,
                                               message.self_mute,
                                               message.self_deaf,
                                               message.priority_speaker,
                                               message.recording)
            self.log.info("User joined: %s" % message.name)
            # We can't just flow into the next section to deal with this, as
            # that would count as a channel change, and it doesn't always work
            # as expected anyway.
            self.channels[message.channel_id].add_user(
                self.users[message.session])
            # Store our User object
            if message.name == self.username:
                self.ourself = self.users[message.session]
                # User connection messages come after all channels have been
                # given, so now is a safe time to attempt to join a channel.
                try:
                    conf = self.config["channel"]
                    if "id" in conf and conf["id"]:
                        if conf["id"] in self.channels:
                            self.join_channel(self.channels[conf["id"]])
                        else:
                            self.log.warning("No channel with id '%s'" %
                                             conf["id"])
                    elif "name" in conf and conf["name"]:
                        chan = self.find_channel_by_name(conf["name"])
                        if chan is not None:
                            self.join_channel(chan)
                        else:
                            self.log.warning("No channel with name '%s'" %
                                             conf["name"])
                    else:
                        self.log.warning("No channel found in config")
                except Exception:
                    self.log.warning("Config is missing 'channel' section")
            else:
                event = mumble_events.UserJoined(self,
                                                 self.users[message.session])
                self.event_manager.run_callback("Mumble/UserJoined", event)
        else:
            # Note: More than one state change can happen at once
            user = self.users[message.session]
            if message.HasField('channel_id'):
                actor = self.users[message.actor]
                self.log.info("User moved channel: %s from %s to %s by %s" %
                              (user,
                               user.channel,
                               self.channels[message.channel_id],
                               actor))
                user.channel.remove_user(user)
                self.channels[message.channel_id].add_user(user)
                user.channel = self.channels[message.channel_id]

                event = mumble_events.UserMoved(self, user, user.channel)
                self.event_manager.run_callback("Mumble/UserMoved", event)
            if message.HasField('mute'):
                actor = self.users[message.actor]
                if message.mute:
                    self.log.info("User was muted: %s by %s" % (user, actor))
                else:
                    self.log.info("User was unmuted: %s by %s" % (user, actor))
                user.mute = message.mute

                event = mumble_events.UserMuteToggle(self, user, user.mute,
                                                     actor)
                self.event_manager.run_callback("Mumble/UserMuteToggle", event)
            if message.HasField('deaf'):
                actor = self.users[message.actor]
                if message.deaf:
                    self.log.info("User was deafened: %s by %s" % (user,
                                                                   actor))
                else:
                    self.log.info("User was undeafened: %s by %s" % (user,
                                                                     actor))
                user.deaf = message.deaf

                event = mumble_events.UserDeafToggle(self, user, user.deaf,
                                                     actor)
                self.event_manager.run_callback("Mumble/UserDeafToggle", event)
            if message.HasField('suppress'):
                if message.suppress:
                    self.log.info("User was suppressed: %s" % user)
                else:
                    self.log.info("User was unsuppressed: %s" % user)
                user.suppress = message.suppress

                event = mumble_events.UserSuppressionToggle(self, user,
                                                            user.suppress)
                self.event_manager.run_callback("Mumble/UserSuppressionToggle",
                                                event)
            if message.HasField('self_mute'):
                if message.self_mute:
                    self.log.info("User muted themselves: %s" % user)
                else:
                    self.log.info("User unmuted themselves: %s" % user)
                user.self_mute = message.self_mute

                event = mumble_events.UserSelfMuteToggle(self, user,
                                                         user.self_mute)
                self.event_manager.run_callback("Mumble/UserSelfMuteToggle",
                                                event)
            if message.HasField('self_deaf'):
                if message.self_deaf:
                    self.log.info("User deafened themselves: %s" % user)
                else:
                    self.log.info("User undeafened themselves: %s" % user)
                user.self_deaf = message.self_deaf

                event = mumble_events.UserSelfDeafToggle(self, user,
                                                         user.self_deaf)
                self.event_manager.run_callback("Mumble/UserSelfDeafToggle",
                                                event)
            if message.HasField('priority_speaker'):
                actor = self.users[message.actor]
                if message.priority_speaker:
                    self.log.info("User was given priority speaker: %s by %s"
                                  % (user, actor))
                else:
                    self.log.info("User was revoked priority speaker: %s by %s"
                                  % (user, actor))
                state = user.priority_speaker = message.priority_speaker

                event = mumble_events.UserPrioritySpeakerToggle(self, user,
                                                                state, actor)
                self.event_manager.run_callback("Mumble/UserPrioritySpeaker"
                                                "Toggle", event)
            if message.HasField('recording'):
                if message.recording:
                    self.log.info("User started recording: %s" % user)
                else:
                    self.log.info("User stopped recording: %s" % user)
                user.recording = message.recording

                event = mumble_events.UserRecordingToggle(self, user,
                                                          user.recording)

    def handle_command(self, source, target, message):
        """
        Handles checking a message for a command.
        """

        cc = self.control_chars.replace("{NICK}", self.username).lower()

        if message.lower().startswith(cc):  # It's a command!
            # Some case-insensitive replacement here.
            regex = re.compile(re.escape(cc), re.IGNORECASE)
            replaced = regex.sub("", message, count=1)

            split = replaced.split()
            command = split[0]
            args = split[1:]

            printable = "<%s> %s" % (source, message)

            event = general_events.PreCommand(self, command, args, source,
                                              target, printable)
            self.event_manager.run_callback("PreCommand", event)

            if event.printable:
                self.log.info(event.printable)

            result = self.command_manager.run_command(event.command,
                                                      event.source,
                                                      event.target, self,
                                                      event.args)
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

    def handle_msg_textmessage(self, message):
        if message.actor in self.users:
            user_obj = self.users[message.actor]
            msg = html_to_text(message.message, True)

            if message.channel_id:
                cid = message.channel_id[0]
                channel_obj = self.channels[cid]
            else:
                # Private message - set the channel_obj (source) to user who
                # sent the message, as is done with IRC (otherwise it would be
                # None).
                channel_obj = user_obj

            if not self.handle_command(user_obj, channel_obj, msg):
                event = general_events.PreMessageReceived(self,
                                                          user_obj,
                                                          channel_obj,
                                                          msg,
                                                          "message",
                                                          printable=True)
                self.event_manager.run_callback("PreMessageReceived", event)
                if event.printable:
                    for line in msg.split("\n"):
                        self.log.info("<%s> %s" % (user_obj, line))

                second_event = general_events.MessageReceived(self,
                                                              user_obj,
                                                              channel_obj,
                                                              event.message,
                                                              "message")
                self.event_manager.run_callback("MessageReceived",
                                                second_event)

            # TODO: Remove this before proper release. An admin plugin with the
            # - same functionality should be created.
            if msg.startswith('!'):
                cmd = msg[1:].lower().split(" ")[0]
                if cmd == "users":
                    self.print_users()
                elif cmd == "channels":
                    self.print_channels()
                elif cmd == "msgme":
                    self.msg_user("msg_user() test using id", message.actor)
                    self.msg_user("msg_user() test using User object",
                                  self.users[message.actor])
                elif cmd == "join":
                    channame = msg[6:]
                    chan = None
                    for _id, channel in self.channels.iteritems():
                        if channel.name.lower() == channame.lower():
                            chan = _id
                            break
                    if chan is None:
                        self.msg_user("Could not find channel", message.actor)
                    else:
                        self.msg_user("Joining channel", message.actor)
                        self.join_channel(chan)

    def msg(self, message, target="channel", target_id=None):
        if target_id is None and target == "channel":
            target_id = self.ourself.channel.channel_id

        self.log.debug("Sending text message: %s" % message)

        message = cgi.escape(message)

        msg = Mumble_pb2.TextMessage()  # session, channel_id, tree_id, message
        msg.message = message
        if target == "channel":
            msg.channel_id.append(target_id)
        else:
            msg.session.append(target_id)

        self.sendProtobuf(msg)

    def msg_channel(self, message, channel):
        if isinstance(channel, Channel):
            channel = channel.channel_id

        event = general_events.MessageSent(self, "message",
                                           self.channels[channel], message)
        self.event_manager.run_callback("MessageSent", event)

        message = event.message

        self.log.info("-> *%s* %s" % (self.channels[channel], message))

        self.msg(message, "channel", channel)

    def msg_user(self, message, user):
        if isinstance(user, User):
            user = user.session

        event = general_events.MessageSent(self, "message",
                                           self.users[user], message)
        self.event_manager.run_callback("MessageSent", event)

        message = event.message

        self.log.info("-> (%s) %s" % (self.users[user], message))

        self.msg(message, "user", user)

    def join_channel(self, channel):
        if isinstance(channel, Channel):
            channel = channel.channel_id
        msg = Mumble_pb2.UserState()
        msg.channel_id = channel
        self.sendProtobuf(msg)

    def find_channel_by_name(self, name):
        name = name.lower()
        for cid, channel in self.channels.iteritems():
            if channel.name.lower() == name:
                return channel
        return None

    def print_users(self):
        # TODO: Remove this debug function once user handling is complete
        def print_indented(s, times=1):
            print ("\t" * times), s
        for user in self.users.itervalues():
            print user
            cn = user.channel.__str__()
            print_indented("Channel: %s" % cn.encode('ascii', 'replace'))
            print_indented("Mute: %s" % user.mute)
            print_indented("Deaf: %s" % user.deaf)
            print_indented("Suppressed: %s" % user.suppress)
            print_indented("Self mute: %s" % user.self_mute)
            print_indented("Self deaf: %s" % user.self_deaf)
            print_indented("Priority speaker: %s" % user.priority_speaker)
            print_indented("Recording: %s" % user.recording)

    def print_channels(self):
        # TODO: Remove this debug function once channel handling is complete
        def get_children_channels(channel_id):
            children = []
            for cid, channel in self.channels.iteritems():
                if channel.parent == channel_id:
                    children.append(cid)
            return children

        def print_channel(channels, channel_id, depth=0):
            print "----" * depth,\
                self.channels[channel_id].__str__().encode('ascii', 'replace')
            # Print users, if any
            if len(self.channels[channel_id].users) > 0:
                print "    " * (depth + 1), "Users {"
                for user in self.channels[channel_id].users:
                    print "    " * (depth + 2), user
                print "    " * (depth + 1), "}"
            # Print sub-channels
            for chan in channels[channel_id]:
                print_channel(channels, chan, depth + 1)

        chans = {}  # Assumes root channel is 0 - not sure if this is ever not
        for cid, chan in self.channels.iteritems():
            chans[cid] = get_children_channels(cid)
        print_channel(chans, 0)
