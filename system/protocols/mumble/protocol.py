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
from user import User
from channel import Channel

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

        reactor.connectSSL(
            self.networking["address"],
            self.networking["port"],
            self.factory,
            ssl.ClientContextFactory(),
            120
        )

    def __call__(self):
        return self

    def recvProtobuf(self, msg_type, message):
        if isinstance(message, Mumble_pb2.Version):
            # version, release, os, os_version
            self.log.info("Connected to Murmur v%s" % message.release)

        elif isinstance(message, Mumble_pb2.CodecVersion):
            # alpha, beta, prefer_alpha, opus
            pass
        elif isinstance(message, Mumble_pb2.CryptSetup):
            # key, client_nonce, server_nonce
            pass
        elif isinstance(message, Mumble_pb2.ChannelState):
            # channel_id, name, position, [parent]
            if not message.channel_id in self.channels:
                parent = None
                if message.HasField('parent'):
                    parent = message.parent
                self.channels[message.channel_id] = Channel(message.channel_id,
                                                            message.name,
                                                            parent)
                self.log.info("New channel: %s" % message.name)
        elif isinstance(message, Mumble_pb2.PermissionQuery):
            # channel_id, permissions
            # TODO: Don't use this for current channel:
            # This checks permission up through the tree of channels, so the
            # last one is not always the current channel.
            # UserState is not always received for channel change though (not
            # on initial join, haven't tested self-move).
            self.current_channel = message.channel_id
            self.log.info("Current channel: %s"
                          % self.channels[self.current_channel].name)
        elif isinstance(message, Mumble_pb2.UserState):
            # session, name,
            # [user_id, suppress, hash, actor, self_mute, self_deaf]
            if message.name and message.session not in self.users:
                # Note: I'm not sure if message.name should ever be empty and
                # not in self.users - rakiru
                self.users[message.session] = User(message.name,
                                                   message.channel_id,
                                                   message.mute,
                                                   message.deaf,
                                                   message.suppress,
                                                   message.self_mute,
                                                   message.self_deaf,
                                                   message.recording)
                self.log.info("User joined: %s" % message.name)
                # Store our session id
                if message.name == self.username:
                    self.session = message.session
            else:
                # Note: More than one state change can happen at once
                user = self.users[message.session]
                if message.HasField('channel_id'):
                    actor = self.users[message.actor]
                    self.log.info("User moved channel: %s from %s to %s by %s"
                                  % (user.name,
                                     self.channels[user.channel_id].name,
                                     self.channels[message.channel_id].name,
                                     actor.name))
                    user.channel_id = message.channel_id
                    # TODO: Fire event here
                if message.HasField('mute'):
                    actor = self.users[message.actor]
                    if message.mute:
                        self.log.info("User was muted: %s by %s" %
                                      (user.name, actor.name))
                    else:
                        self.log.info("User was unmuted: %s by %s" %
                                      (user.name, actor.name))
                    user.mute = message.mute
                    # TODO: Fire event here
                if message.HasField('deaf'):
                    actor = self.users[message.actor]
                    if message.deaf:
                        self.log.info("User was deafened: %s by %s" %
                                      (user.name, actor.name))
                    else:
                        self.log.info("User was undeafened: %s by %s" %
                                      (user.name, actor.name))
                    user.deaf = message.deaf
                    # TODO: Fire event here
                if message.HasField('suppress'):
                    if message.suppress:
                        self.log.info("User was suppressed: %s" % user.name)
                    else:
                        self.log.info("User was unsuppressed: %s" % user.name)
                    user.suppress = message.suppress
                    # TODO: Fire event here
                if message.HasField('self_mute'):
                    if message.self_mute:
                        self.log.info("User muted themselves: %s" % user.name)
                    else:
                        self.log.info("User unmuted themselves: %s" %
                                      user.name)
                    user.self_mute = message.self_mute
                    # TODO: Fire event here
                if message.HasField('self_deaf'):
                    if message.self_deaf:
                        self.log.info("User deafened themselves: %s" %
                                      user.name)
                    else:
                        self.log.info("User undeafened themselves: %s" %
                                      user.name)
                    user.self_deaf = message.self_deaf
                    # TODO: Fire event here
                if message.HasField('recording'):
                    if message.recording:
                        self.log.info("User started recording: %s" % user.name)
                    else:
                        self.log.info("User stopped recording: %s" % user.name)
                    user.recording = message.recording
                    # TODO: Fire event here
        elif isinstance(message, Mumble_pb2.ServerSync):
            # session, max_bandwidth, welcome_text, permissions
            welcome_text = html_to_text(message.welcome_text, True)
            self.log.info("===   Welcome message   ===")
            for line in welcome_text.split("\n"):
                self.log.info(line)
            self.log.info("=== End welcome message ===")
        elif isinstance(message, Mumble_pb2.ServerConfig):
            # allow_html, message_length, image_message_length
            self.allow_html = message.allow_html
            pass
        elif isinstance(message, Mumble_pb2.Ping):
            # timestamp, good, late, lost, resync
            pass
        elif isinstance(message, Mumble_pb2.UserRemove):
            # session
            if message.session in self.users:
                self.log.info("User left: %s" %
                              self.users[message.session].name)
                del self.users[message.session]
        elif isinstance(message, Mumble_pb2.TextMessage):
            # actor, channel_id, message
            if message.actor in self.users:
                msg = html_to_text(message.message, True)
                for line in msg.split("\n"):
                    self.log.info("<%s> %s" %
                                  (self.users[message.actor].name, line
                                   ))
        else:
            self.log.debug("Unknown message type: %s" % message.__class__)
            self.log.debug("Received message '%s' (%d):\n%s"
                           % (message.__class__, msg_type, str(message)))

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
        version.os_version = "Mumble 1.2.3 Twisted Protocol"

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

    def init_ping(self):
        # Call ping every PING_REPEAT_TIME seconds.
        reactor.callLater(Protocol.PING_REPEAT_TIME, self.ping_handler)

    def ping_handler(self):
        self.log.debug("Sending ping")

        # Ping has only optional data, no required
        ping = Mumble_pb2.Ping()
        self.sendProtobuf(ping)

        self.init_ping()

    def msg(self, message, target="channel", target_id=None):
        if target_id is None and target == "channel":
            target_id = self.current_channel

        self.log.debug("Sending text message: %s" % message)

        msg = Mumble_pb2.TextMessage()  # session, channel_id, tree_id, message
        msg.message = message
        if target == "channel":
            msg.channel_id.append(target_id)
        else:
            msg.session.append(target_id)

        # self.sendProtobuf(msg)

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
            except Exception:
                self.log.error("Exception while handling data.")
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
