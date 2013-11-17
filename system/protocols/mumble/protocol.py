#!/usr/bin/env python
# coding=utf-8

__author__ = 'Gareth Coles'

# This is a modified version of Chaosteil's open-domain Mumble library.
# The original code can be found on GitHub, at the following link..
# https://github.com/Chaosteil/rdiablo-mumble-bot/blob/master/
# File: mumble_protocol.py


import logging
import platform
import struct

import Mumble_pb2

from twisted.internet import reactor, protocol, ssl

from utils.log import getLogger
from utils.html import html_to_text
from system.protocols.mumble.user import User
from system.protocols.mumble.channel import Channel

log = logging.getLogger(__name__)


class Protocol(protocol.Protocol):
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

    def __init__(self, factory, config):
        self.received = ""
        self.factory = factory
        self.config = config
        self.log = getLogger("Mumble")
        self.log.info("Setting up..")

        self.username = config["identity"]["username"]
        self.password = config["identity"]["password"]
        self.networking = config["network"]
        self.tokens = config["identity"]["tokens"]

        # TODO: Throw event (General, post-setup, pre-connect)

        reactor.connectSSL(
            self.networking["address"],
            self.networking["port"],
            self.factory,
            ssl.ClientContextFactory(),
            120
        )

        # TODO: Throw event (General, post-connect)

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

        # Then we initialize our ping handler
        self.init_ping()

        # Then we mute ourselves to prevent errors with voice packets
        message = Mumble_pb2.UserState()
        message.self_mute = True
        message.self_deaf = True

        self.sendProtobuf(message)

        # TODO: Throw event

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
                self.log.debug(e)
                # We abort on exception, because that's the proper thing to do
                #self.transport.loseConnection()
                #raise

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
            # TODO: Throw event (General, post-setup)
        elif isinstance(message, Mumble_pb2.Reject):
            # version, release, os, os_version
            self.log.info("Could not connect to server: %s - %s" %
                          (message.type, message.reason))
            # TODO: Kill connection, stop ping loop, etc
        elif isinstance(message, Mumble_pb2.CodecVersion):
            # alpha, beta, prefer_alpha, opus

            # TODO: Throw event (Mumble, codec version)
            pass
        elif isinstance(message, Mumble_pb2.CryptSetup):
            # key, client_nonce, server_nonce

            # TODO: Throw event (Mumble, crypto setup)
            pass
        elif isinstance(message, Mumble_pb2.ChannelState):
            # channel_id, name, position, [parent]
            self.handle_msg_channelstate(message)

            # TODO: Throw event (Mumble, channel state)
        elif isinstance(message, Mumble_pb2.PermissionQuery):
            # channel_id, permissions
            pass
            # TODO: Throw event (Mumble, permissions query)
        elif isinstance(message, Mumble_pb2.UserState):
            # session, name,
            # [user_id, suppress, hash, actor, self_mute, self_deaf]
            self.handle_msg_userstate(message)

            # TODO: Throw event (Mumble, user state)
            # Is that necessary? ^ Events are thrown for each user state change
            # anyway in handle_msg_userstate(), and if a plugin needs something
            # we don't yet track, then we should add support for it instead of
            # giving them raw user state information.
        elif isinstance(message, Mumble_pb2.ServerSync):
            # session, max_bandwidth, welcome_text, permissions
            welcome_text = html_to_text(message.welcome_text, True)
            self.log.info("===   Welcome message   ===")
            for line in welcome_text.split("\n"):
                self.log.info(line)
            self.log.info("=== End welcome message ===")

            # TODO: Throw event (Mumble, server sync)
        elif isinstance(message, Mumble_pb2.ServerConfig):
            # allow_html, message_length, image_message_length
            self.allow_html = message.allow_html

            # TODO: Throw event
        elif isinstance(message, Mumble_pb2.Ping):
            # timestamp, good, late, lost, resync
            pass

            # TODO: Throw event
        elif isinstance(message, Mumble_pb2.UserRemove):
            # session
            if message.session in self.users:
                user = self.users[message.session]
                self.log.info("User left: %s" %
                              user)
                user.channel.remove_user(user)
                del self.users[message.session]

            # TODO: Throw event
        elif isinstance(message, Mumble_pb2.TextMessage):
            # actor, channel_id, message
            self.handle_msg_textmessage(message)

            # TODO: Throw event
        else:
            self.log.debug("Unknown message type: %s" % message.__class__)
            self.log.debug("Received message '%s' (%d):\n%s"
                           % (message.__class__, msg_type, str(message)))

            # TODO: Throw event

    def init_ping(self):
        # Call ping every PING_REPEAT_TIME seconds.
        reactor.callLater(Protocol.PING_REPEAT_TIME, self.ping_handler)

        # TODO: Throw event

    def ping_handler(self):
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
                # TODO: Throw event
        if message.links_remove:
            for link in message.links_remove:
                self.channels[message.channel_id].remove_link(link)
                self.log.info("Channel link removed: %s from %s" %
                              (self.channels[link],
                               self.channels[message.channel_id]))
                # TODO: Throw event

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
                except:
                    self.log.warning("Config is missing 'channel' section")
            else:
                # TODO: Throw event - user join
                pass
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

                # TODO: Throw event
            if message.HasField('mute'):
                actor = self.users[message.actor]
                if message.mute:
                    self.log.info("User was muted: %s by %s" % (user, actor))
                else:
                    self.log.info("User was unmuted: %s by %s" % (user, actor))
                user.mute = message.mute
                # TODO: Throw event
            if message.HasField('deaf'):
                actor = self.users[message.actor]
                if message.deaf:
                    self.log.info("User was deafened: %s by %s" % (user,
                                                                   actor))
                else:
                    self.log.info("User was undeafened: %s by %s" % (user,
                                                                     actor))
                user.deaf = message.deaf
                # TODO: Throw event
            if message.HasField('suppress'):
                if message.suppress:
                    self.log.info("User was suppressed: %s" % user)
                else:
                    self.log.info("User was unsuppressed: %s" % user)
                user.suppress = message.suppress
                # TODO: Throw event
            if message.HasField('self_mute'):
                if message.self_mute:
                    self.log.info("User muted themselves: %s" % user)
                else:
                    self.log.info("User unmuted themselves: %s" % user)
                user.self_mute = message.self_mute
                # TODO: Throw event
            if message.HasField('self_deaf'):
                if message.self_deaf:
                    self.log.info("User deafened themselves: %s" % user)
                else:
                    self.log.info("User undeafened themselves: %s" % user)
                user.self_deaf = message.self_deaf
                # TODO: Throw event
            if message.HasField('priority_speaker'):
                actor = self.users[message.actor]
                if message.priority_speaker:
                    self.log.info("User was given priority speaker: %s by %s"
                                  % (user, actor))
                else:
                    self.log.info("User was revoked priority speaker: %s by %s"
                                  % (user, actor))
                user.priority_speaker = message.priority_speaker
                # TODO: Throw event
            if message.HasField('recording'):
                if message.recording:
                    self.log.info("User started recording: %s" % user)
                else:
                    self.log.info("User stopped recording: %s" % user)
                user.recording = message.recording
                # TODO: Throw event

    def handle_msg_textmessage(self, message):
        if message.actor in self.users:
            msg = html_to_text(message.message, True)
            for line in msg.split("\n"):
                self.log.info("<%s> %s" % (self.users[message.actor],
                                           line))
            # TODO: Throw event
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

        # TODO: Throw event
        if target_id is None and target == "channel":
            target_id = self.ourself.channel.channel_id

        self.log.debug("Sending text message: %s" % message)

        msg = Mumble_pb2.TextMessage()  # session, channel_id, tree_id, message
        msg.message = message
        if target == "channel":
            msg.channel_id.append(target_id)
        else:
            msg.session.append(target_id)

        self.sendProtobuf(msg)

        # TODO: Throw event

    def msg_channel(self, message, channel):

        # TODO: Throw event
        if isinstance(channel, Channel):
            channel = channel.channel_id
        self.msg(message, "channel", channel)

        # TODO: Throw event

    def msg_user(self, message, user):

        # TODO: Throw event
        if isinstance(user, User):
            user = user.session
        self.msg(message, "user", user)

        # TODO: Throw event

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
