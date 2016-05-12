# coding=utf-8
import cgi
import os
import platform
import struct

from twisted.internet import reactor, ssl, task

from system.commands.manager import CommandManager

from system.enums import CommandState

from system.events.manager import EventManager
from system.events import general as general_events
from system.events import mumble as mumble_events

from system.logging.logger import getLogger

from system.protocols.capabilities import Capabilities

from system.protocols.generic.protocol import SingleChannelProtocol

from system.protocols.mumble import Mumble_pb2
from system.protocols.mumble.user import User
from system.protocols.mumble.channel import Channel
from system.protocols.mumble.acl import Perms
from system.protocols.mumble.structs import Version

from system.translations import Translations

from utils.html import html_to_text
from utils.protobuf import decode_varint
from utils.switch import Switch
__author__ = 'Gareth Coles'

# This is a modified version of Chaosteil's open-domain Mumble library.
# The original code can be found on GitHub, at the following link..
# https://github.com/Chaosteil/rdiablo-mumble-bot/
_ = Translations().get()


class Protocol(SingleChannelProtocol):

    TYPE = "mumble"
    CAPABILITIES = (
        Capabilities.MULTIPLE_CHANNELS,
        Capabilities.MULTILINE_MESSAGE,
        Capabilities.MESSAGE_UNJOINED_CHANNELS,
        Capabilities.VOICE,
    )

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
        Mumble_pb2.ServerConfig,
        Mumble_pb2.SuggestConfig
    ]

    # Reversing the IDs, so we are able to backreference.
    MESSAGE_ID = dict([(v, k) for k, v in enumerate(ID_MESSAGE)])

    PING_REPEAT_TIME = 5

    channels = {}
    users = {}
    _acls = {}

    @property
    def num_channels(self):
        return len(self.channels)

    control_chars = "."

    pinging = True

    ourselves = None

    use_cgi = True

    def __init__(self, name, factory, config):
        self.name = name
        self.factory = factory
        self.config = config

        self.received = ""
        self.log = getLogger(self.name)
        self.log.info("Setting up..")

        self.command_manager = CommandManager()
        self.event_manager = EventManager()

        self.username = config["identity"]["username"]
        self.password = config["identity"]["password"]
        self.networking = config["network"]
        self.tokens = config["identity"]["tokens"]

        self.control_chars = config["control_chars"]

        audio_conf = config.get("audio", {})
        self.should_mute_self = audio_conf.get("should_mute_self", True)
        self.should_deafen_self = audio_conf.get("should_deafen_self", True)

        self.userstats_request_rate = config.get("userstats_request_rate", 60)

    def _get_client_context(self):
        # Check if a cert file is specified in config
        if ("certificate" in self.config["identity"] and
                self.config["identity"]["certificate"]):
            # Attempt to load it
            try:
                self.log.debug(_("Attempting to load certificate file"))
                from OpenSSL import crypto, SSL
                cert_file = self.config["identity"]["certificate"]
                # Check if cert file exists, and if not, create it
                if not os.path.exists(cert_file):
                    self.log.info(_("Certificate file does not exist - "
                                    "generating..."))
                    # Creates a key similarly to the official mumble client
                    pkey = crypto.PKey()
                    pkey.generate_key(crypto.TYPE_RSA, 2048)
                    cert = crypto.X509()
                    cert.set_version(2)
                    cert.set_serial_number(1000)
                    cert.gmtime_adj_notBefore(0)
                    cert.gmtime_adj_notAfter(60 * 60 * 24 * 365 * 20)
                    cert.set_pubkey(pkey)
                    cert.get_subject().CN = self.username
                    cert.set_issuer(cert.get_subject())
                    cert.add_extensions([
                        crypto.X509Extension("basicConstraints", True,
                                             "CA:FALSE"),
                        crypto.X509Extension("extendedKeyUsage", False,
                                             "clientAuth"),
                        # The official Mumble client does this, but it errors
                        # here, and I'm not sure it's required for certs where
                        # CA is FALSE (RFC 3280, 4.2.1.2)
                        # crypto.X509Extension("subjectKeyIdentifier", False,
                        #                      "hash"),
                        crypto.X509Extension("nsComment", False,
                                             "Generated by Ultros"),
                    ])
                    cert.sign(pkey, "sha1")
                    p12 = crypto.PKCS12()
                    p12.set_privatekey(pkey)
                    p12.set_certificate(cert)
                    cert_file_dir = os.path.dirname(cert_file)
                    if not os.path.exists(cert_file_dir):
                        self.log.debug("Creating directories for cert file")
                        os.makedirs(cert_file_dir)
                    with open(cert_file, "wb") as cert_file_handle:
                        cert_file_handle.write(p12.export())

                # Load the cert file
                with open(cert_file, "rb") as cert_file_handle:
                    certificate = crypto.load_pkcs12(cert_file_handle.read())

                # Context factory class, using the loaded cert
                class CtxFactory(ssl.ClientContextFactory):
                    def getContext(self):
                        self.method = SSL.SSLv23_METHOD
                        ctx = ssl.ClientContextFactory.getContext(self)
                        ctx.use_certificate(certificate.get_certificate())
                        ctx.use_privatekey(certificate.get_privatekey())
                        return ctx

                self.log.info(_("Loaded specified certificate file"))
                return CtxFactory()
            except ImportError:
                self.log.error(_("Could not import OpenSSL - cannot connect "
                                 "with certificate file"))
            except IOError:
                self.log.error(_("Could not load cert file"))
                self.log.debug("Exception info:", exc_info=1)
            except Exception:
                self.log.exception(_("Unknown error while loading certificate "
                                     "file"))
            return None
        else:
            # Default CtxFactory for no certificate
            self.log.info(_("No certificate specified - connecting without "
                            "certificate"))
            return ssl.ClientContextFactory()

    def shutdown(self):
        self.msg(_("Disconnecting: Protocol shutdown"))
        self.stop_userstats_requests()
        self.transport.loseConnection()

    def connectionMade(self):
        self.log.info(_("Connected to server."))

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

        # Then we initialize our looping handlers
        self.init_ping()
        self.start_userstats_requests()

        # Mute/deafen ourselves if wanted (saves processing UDP packets if not
        # needed)
        message = Mumble_pb2.UserState()
        message.self_mute = self.should_mute_self
        message.self_deaf = self.should_deafen_self

        self.sendProtobuf(message)

        self.factory.clientConnected()

    def connectionLost(self, reason=None):
        self.pinging = False
        self.stop_userstats_requests()

    def dataReceived(self, recv):
        # Append our received data
        self.received = self.received + recv

        # If we have enough bytes to read the header, we do that
        while len(self.received) >= Protocol.PREFIX_LENGTH:
            msg_type, length = \
                struct.unpack(Protocol.PREFIX_FORMAT,
                              self.received[:Protocol.PREFIX_LENGTH])

            full_length = Protocol.PREFIX_LENGTH + length

            self.log.trace("Length: %d" % length)
            self.log.trace("Message type: %d" % msg_type)

            # Check if this this a valid message ID
            if msg_type not in Protocol.MESSAGE_ID.values():
                self.log.error(_("Message ID not available."))
                self.transport.loseConnection()
                return

            # We need to check if we have enough bytes to fully read the
            # message
            if len(self.received) < full_length:
                self.log.trace(_("Need to fill data"))
                return

            # Read and handle the specific message
            if msg_type == 1:
                # Non-Protobuf messages
                # 1 is taken from the position of UDPTunnel in ID_MESSAGE
                self.recv_UDP(self.received[Protocol.PREFIX_LENGTH:
                                            Protocol.PREFIX_LENGTH + length])
            else:
                # Regular (Protobuf) messages
                msg = Protocol.ID_MESSAGE[msg_type]()
                msg.ParseFromString(
                    self.received[Protocol.PREFIX_LENGTH:
                                  Protocol.PREFIX_LENGTH + length])

                # Handle the message
                try:
                    self.recvProtobuf(msg_type, msg)
                except Exception:
                    self.log.exception(_("Exception while handling data."))

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
            self.log.info(_("Connected to Murmur v%s") % message.release)
            event = general_events.PostSetupEvent(self, self.config)
            self.event_manager.run_callback("PostSetup", event)
        elif isinstance(message, Mumble_pb2.Reject):
            # version, release, os, os_version
            self.log.info(_("Could not connect to server: %s - %s") %
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
            self.set_permissions(channel, permissions, flush)
            self.log.trace("PermissionQuery received: channel: '%s', "
                           "permissions: '%s', flush:'%s'" %
                           (channel,
                            Perms.get_permissions_names(permissions),
                            flush))
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
            # TODO: Store this?
            max_bandwidth = message.max_bandwidth
            permissions = message.permissions
            # TODO: Check this permissions relevancy - root chan? We don't know
            # what channel we're in yet, so it must be
            self.set_permissions(0, permissions)
            welcome_text = html_to_text(message.welcome_text, True)
            self.log.info(_("===   Welcome message   ==="))
            self.log.trace("ServerSync received: max_bandwidth: '%s', "
                           "permissions: '%s', welcome text: [below]" %
                           (max_bandwidth,
                            Perms.get_permissions_names(permissions)))
            for line in welcome_text.split("\n"):
                self.log.info(line)
            self.log.info(_("=== End welcome message ==="))

            event = mumble_events.ServerSync(self, session, max_bandwidth,
                                             welcome_text, permissions)
            self.event_manager.run_callback("Mumble/ServerSync", event)
        elif isinstance(message, Mumble_pb2.ServerConfig):
            # max_bandwidth, welcome_text, allow_html, message_length,
            # image_message_length
            # TODO: Store these
            max_bandwidth = message.max_bandwidth
            welcome_text = message.welcome_text
            self.allow_html = message.allow_html
            message_length = message.message_length
            image_message_length = message.image_message_length

            event = mumble_events.ServerConfig(self, max_bandwidth,
                                               welcome_text, self.allow_html,
                                               message_length,
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
                user.is_tracked = False
                self.log.info(_("User left: %s") %
                              user)
                user.channel.remove_user(user)
                del self.users[message.session]
            else:
                user = None

            if actor in self.users:
                event = mumble_events.UserRemove(self, session, actor, user,
                                                 reason, ban,
                                                 self.users[actor])
                self.event_manager.run_callback("Mumble/UserRemove", event)

            s_event = general_events.UserDisconnected(self, user)
            self.event_manager.run_callback("UserDisconnected", s_event)
        elif isinstance(message, Mumble_pb2.TextMessage):
            # actor, channel_id, message
            self.handle_msg_textmessage(message)
        elif isinstance(message, Mumble_pb2.UserStats):
            self.handle_msg_userstats(message)
        else:
            self.log.trace(_("Unknown message type: %s") % message.__class__)
            self.log.trace(_("Received message '%s' (%d):\n%s")
                           % (message.__class__, msg_type, str(message)))

            event = mumble_events.Unknown(self, type(message), message)
            self.event_manager.run_callback("Mumble/Unknown", event)

    def recv_UDP(self, data):
        """
        Handle a UDP message (whether it be from actual UDP or via TCP tunnel)
        :param data: UDP
        """
        # TODO: Use UDP rather than TCP tunnel (see protocol docs section 5)
        # We don't actually need to parse this atm
        return
        _first_byte = ord(data[0])
        msg_type = (_first_byte & 0xE0) >> 5
        target = _first_byte & 0x1F
        pos = 1
        session, pos = decode_varint(data, pos)
        sequence, pos = decode_varint(data, pos)
        self.log.trace(
            "UDP Message: Type=%s, target=%s, session=%s, sequence=%s",
            msg_type,
            target,
            self.get_user(session),
            sequence
        )
        # TEMP: Forward the packet back to the server

        msg_data = data

        length = len(msg_data)

        # Compile the data with the header
        data = struct.pack(Protocol.PREFIX_FORMAT, 1, length) + msg_data

        # Send the data
        # self.transport.write(data)

    def init_ping(self):
        # Call ping every PING_REPEAT_TIME seconds.
        reactor.callLater(Protocol.PING_REPEAT_TIME, self.ping_handler)

    def ping_handler(self):
        if not self.pinging:
            return
        self.log.trace("Sending ping")

        # Ping has only optional data, no required
        ping = Mumble_pb2.Ping()
        self.sendProtobuf(ping)

        self.init_ping()

    def start_userstats_requests(self):
        self._userstats_requests_task = task.LoopingCall(
            self.userstats_request_handler
        )
        self._userstats_requests_task.start(self.userstats_request_rate, False)

    def stop_userstats_requests(self):
        if self._userstats_requests_task and \
                self._userstats_requests_task.running:
            self._userstats_requests_task.stop()

    def userstats_request_handler(self):
        try:
            for user in self.users.itervalues():
                self.request_userstats(user, True)
        except Exception:
            self.log.exception("Error in UserStats request loop")

    def handle_msg_channelstate(self, message):
        if message.channel_id not in self.channels:
            parent = None
            if message.HasField('parent'):
                parent = message.parent
            links = []
            if message.links:
                links = list(message.links)
                for link in links:
                    self.log.debug(_("Channel link: %s to %s") %
                                   (self.channels[link],
                                    self.channels[message.channel_id]))
            self.channels[message.channel_id] = Channel(self,
                                                        message.channel_id,
                                                        message.name,
                                                        parent,
                                                        message.position,
                                                        links)
            self.log.info(_("New channel: %s") % message.name)
        if message.links_add:
            for link in message.links_add:
                self.channels[message.channel_id].add_link(link)
                self.log.info(_("Channel link added: %s to %s") %
                              (self.channels[link],
                               self.channels[message.channel_id]))

                # TOTALLY MORE READABLE
                # GOOD JOB PEP8
                event = mumble_events.ChannelLinked(self, self.channels[link],
                                                    self.channels
                                                    [message.channel_id])
                self.event_manager.run_callback("Mumble/ChannelLinked", event)
        if message.links_remove:
            for link in message.links_remove:
                self.channels[message.channel_id].remove_link(link)
                self.log.info(_("Channel link removed: %s from %s") %
                              (self.channels[link],
                               self.channels[message.channel_id]))

                # Jesus fuck.
                event = mumble_events.ChannelUnlinked(self, self.channels
                                                      [link], self.channels
                                                      [message.channel_id])
                self.event_manager.run_callback("Mumble/ChannelUnlinked",
                                                event)

    def handle_msg_userstate(self, message):
        if message.name and message.session not in self.users:
            # Note: I'm not sure if message.name should ever be empty and
            # not in self.users - rakiru
            # Note: RE: above note - Mumble desktop client source suggests not.
            user = User(self,
                        message.session,
                        message.name,
                        self.channels[message.channel_id],
                        message.mute,
                        message.deaf,
                        message.suppress,
                        message.self_mute,
                        message.self_deaf,
                        message.priority_speaker,
                        message.recording)
            self.users[message.session] = user

            # TODO: plugin_identity and plugin_context
            # TODO: Handle comments and avatars properly
            if message.HasField("comment_hash"):
                user.comment_hash = message.comment_hash
            if message.HasField("comment"):
                user.comment = message.comment
            if message.HasField("texture_hash"):
                user.avatar_hash = message.texture_hash
            if message.HasField("texture"):
                user.avatar = message.texture

            if message.HasField("user_id"):
                user_id = message.user_id
                if user_id == 4294967295:
                    # This should never happen, but things will break if it
                    # does. See comment below for explanation of 4294967295.
                    user_id = -1
                user.user_id = user_id

            if message.HasField("hash"):
                user.certificate_hash = message.hash

            self.log.info(_("User joined: %s") % message.name)

            # We can't just flow into the next section to deal with this, as
            # that would count as a channel change, and it doesn't always work
            # as expected anyway.
            self.channels[message.channel_id].add_user(user)

            # Store our User object
            if message.name == self.username:
                self.ourselves = user
                # User connection messages come after all channels have been
                # given, so now is a safe time to attempt to join a channel.
                try:
                    conf = self.config["channel"]
                    if "id" in conf and conf["id"] is not None:
                        cid = conf["id"]
                        if not isinstance(cid, int):
                            try:
                                cid = int(cid)
                            except ValueError:
                                self.log.error(
                                    "Channel ID in config must be a number."
                                )
                            else:
                                self.log.warning(
                                    "Channel ID in config should be a number."
                                )
                        if cid in self.channels:
                            self.join_channel(self.channels[cid])
                        else:
                            self.log.warning(_("No channel with id '%s'") %
                                             cid)
                    elif "name" in conf and conf["name"]:
                        chan = self.get_channel(conf["name"])
                        if chan is not None:
                            self.join_channel(chan)
                        else:
                            self.log.warning(_("No channel with name '%s'") %
                                             conf["name"])
                    else:
                        self.log.warning(_("No channel found in config"))
                except Exception:
                    self.log.warning(_("Config is missing 'channel' section"))
            else:
                event = mumble_events.UserJoined(self, user)
                self.event_manager.run_callback("Mumble/UserJoined", event)

            # Request initial UserStats
            self.request_userstats(user, False)
        else:
            # Note: More than one state change can happen at once
            user = self.users[message.session]
            if message.HasField("actor"):
                actor = self.users[message.actor]
            else:
                actor = None
            if message.HasField('channel_id'):
                self.log.info(_("User moved channel: %s from %s to %s by %s") %
                              (user,
                               user.channel,
                               self.channels[message.channel_id],
                               actor))
                old = self.channels[user.channel.channel_id]
                user.channel.remove_user(user)
                self.channels[message.channel_id].add_user(user)
                user.channel = self.channels[message.channel_id]

                event = mumble_events.UserMoved(self, user, user.channel, old)
                self.event_manager.run_callback("Mumble/UserMoved", event)
            if message.HasField('mute'):
                if message.mute:
                    self.log.info(_("User was muted: %s by %s")
                                  % (user, actor))
                else:
                    self.log.info(_("User was unmuted: %s by %s")
                                  % (user, actor))
                user.mute = message.mute

                event = mumble_events.UserMuteToggle(self, user, user.mute,
                                                     actor)
                self.event_manager.run_callback("Mumble/UserMuteToggle", event)
            if message.HasField('deaf'):
                if message.deaf:
                    self.log.info(_("User was deafened: %s by %s") % (user,
                                                                      actor))
                else:
                    self.log.info(_("User was undeafened: %s by %s") % (user,
                                                                        actor))
                user.deaf = message.deaf

                event = mumble_events.UserDeafToggle(self, user, user.deaf,
                                                     actor)
                self.event_manager.run_callback("Mumble/UserDeafToggle", event)
            if message.HasField('suppress'):
                if message.suppress:
                    self.log.info(_("User was suppressed: %s") % user)
                else:
                    self.log.info(_("User was unsuppressed: %s") % user)
                user.suppress = message.suppress

                event = mumble_events.UserSuppressionToggle(self, user,
                                                            user.suppress)
                self.event_manager.run_callback("Mumble/UserSuppressionToggle",
                                                event)
            if message.HasField('self_mute'):
                if message.self_mute:
                    self.log.info(_("User muted themselves: %s") % user)
                else:
                    self.log.info(_("User unmuted themselves: %s") % user)
                user.self_mute = message.self_mute

                event = mumble_events.UserSelfMuteToggle(self, user,
                                                         user.self_mute)
                self.event_manager.run_callback("Mumble/UserSelfMuteToggle",
                                                event)
            if message.HasField('self_deaf'):
                if message.self_deaf:
                    self.log.info(_("User deafened themselves: %s") % user)
                else:
                    self.log.info(_("User undeafened themselves: %s") % user)
                user.self_deaf = message.self_deaf

                event = mumble_events.UserSelfDeafToggle(self, user,
                                                         user.self_deaf)
                self.event_manager.run_callback("Mumble/UserSelfDeafToggle",
                                                event)
            if message.HasField('priority_speaker'):
                if message.priority_speaker:
                    self.log.info(_("User was given priority speaker: %s by "
                                    "%s")
                                  % (user, actor))
                else:
                    self.log.info(_("User was revoked priority speaker: %s by "
                                    "%s")
                                  % (user, actor))
                state = user.priority_speaker = message.priority_speaker

                event = mumble_events.UserPrioritySpeakerToggle(self, user,
                                                                state, actor)
                self.event_manager.run_callback("Mumble/UserPrioritySpeaker" +
                                                "Toggle", event)
            if message.HasField('recording'):
                if message.recording:
                    self.log.info(_("User started recording: %s") % user)
                else:
                    self.log.info(_("User stopped recording: %s") % user)
                user.recording = message.recording

                event = mumble_events.UserRecordingToggle(self, user,
                                                          user.recording)
                self.event_manager.run_callback("Mumble/UserRecordingToggle",
                                                event)
            # TODO: Events
            # - Comments/avatars may want higher level events. For example, we
            # - may want to automatically request the full comment/avatar if we
            # - get a hash, and only provide an API for the full thing.
            if message.HasField("comment_hash"):
                user.comment_hash = message.comment_hash
            if message.HasField("comment"):
                user.comment = message.comment
            if message.HasField("texture_hash"):
                user.avatar_hash = message.texture_hash
            if message.HasField("texture"):
                user.avatar = message.texture

            if message.HasField("user_id"):
                user_id = message.user_id
                if user_id == 4294967295:
                    # Mumble uses -1 internally, but the field on the message
                    # is a uint32, so we get that instead. We'll use -1 too.
                    user_id = -1
                old_user_id = user.user_id
                user.user_id = user_id
                if user_id >= 0:
                    self.log.info("User was registered: {} by {}",
                                  user, user_id, actor)
                    event = mumble_events.UserRegistered(self, user,
                                                         user_id, actor)
                    event_type = "Mumble/UserRegistered"
                else:
                    self.log.info("User was unregistered: {} by {}",
                                  user, user_id, actor)
                    event = mumble_events.UserUnregistered(self, user,
                                                           old_user_id, actor)
                    event_type = "Mumble/UserUnregistered"
                self.event_manager.run_callback(event_type, event)

    def handle_msg_textmessage(self, message):
        if message.actor in self.users:
            user_obj = self.users[message.actor]
            # TODO: Replace this with proper formatting stuff when implemented
            # Perhaps a new command-handler/event parameter for raw and parsed
            msg = html_to_text(message.message, True)

            if message.channel_id:
                cid = message.channel_id[0]
                channel_obj = self.channels[cid]
            else:
                # Private message - set the channel_obj (source) to user who
                # sent the message, as is done with IRC (otherwise it would be
                # None).
                channel_obj = user_obj

            event = general_events.PreMessageReceived(
                self, user_obj, channel_obj, msg, "message"
            )
            self.event_manager.run_callback("PreMessageReceived", event)
            if event.printable:
                for line in event.message.split("\n"):
                    self.log.info("<%s> %s" % (user_obj, line))

            if not event.cancelled:
                result = self.command_manager.process_input(
                    event.message, user_obj, channel_obj, self,
                    self.control_chars, self.nickname
                )

                for case, default in Switch(result[0]):
                    if case(CommandState.RateLimited):
                        self.log.debug("Command rate-limited")
                        user_obj.respond("That command has been rate-limited, "
                                         "please try again later.")
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
                        user_obj.respond("Error running command: %s"
                                         % result[1])
                        return  # It was a command
                    if default:
                        self.log.debug("Unknown command state: %s" % result[0])
                        break

                second_event = general_events.MessageReceived(
                    self, user_obj, channel_obj, msg, "message"
                )

                self.event_manager.run_callback(
                    "MessageReceived", second_event
                )

    def handle_msg_userstats(self, message):
        user = self.users[message.session]

        # Not sure if this would ever go over UDP, but if it does, then it's
        # possible to arrive after the user has disconnected.
        if user is None:
            self.log.warning(
                "Received UserStats message for non-existent user"
            )
            return

        # You'd think the stats_only flag would avoid us having to do all these
        # HasField checks, but the server doesn't appear to ever send it.
        # There are some fields that appear to exist or not in a group, but
        # I'm not certain if that's always the case, and 3rd party
        # implementations may do it differently anyway.

        if len(message.certificates):
            user.certificates = list(message.certificates)
        if message.HasField("version"):
            user.version = Version(
                message.version.version,
                message.version.release,
                message.version.os,
                message.version.os_version
            )
        if len(message.celt_versions):
            user.celt_versions = list(message.celt_versions)
        if message.HasField("address"):
            user.address = message.address
        if message.HasField("strong_certificate"):
            user.strong_certificate = message.strong_certificate
        if message.HasField("opus"):
            user.opus = message.opus

        if message.HasField("from_client"):
            stats = user.packet_stats_from_client
            if message.from_client.HasField("good"):
                stats.good = message.from_client.good
            if message.from_client.HasField("late"):
                stats.late = message.from_client.late
            if message.from_client.HasField("lost"):
                stats.lost = message.from_client.lost
            if message.from_client.HasField("resync"):
                stats.resync = message.from_client.resync

        if message.HasField("from_server"):
            stats = user.packet_stats_from_server
            if message.from_server.HasField("good"):
                stats.good = message.from_server.good
            if message.from_server.HasField("late"):
                stats.late = message.from_server.late
            if message.from_server.HasField("lost"):
                stats.lost = message.from_server.lost
            if message.from_server.HasField("resync"):
                stats.resync = message.from_server.resync

        if message.HasField("udp_packets"):
            user.udp_packets_sent = message.udp_packets
        if message.HasField("tcp_packets"):
            user.tcp_packets_sent = message.tcp_packets

        if message.HasField("udp_ping_avg"):
            user.udp_ping_avg = message.udp_ping_avg
        if message.HasField("udp_ping_var"):
            user.udp_ping_var = message.udp_ping_var
        if message.HasField("tcp_ping_avg"):
            user.tcp_ping_avg = message.tcp_ping_avg
        if message.HasField("tcp_ping_var"):
            user.tcp_ping_var = message.tcp_ping_var

        if message.HasField("onlinesecs"):
            user.online_time = message.onlinesecs
        if message.HasField("idlesecs"):
            user.idle_time = message.idlesecs

        event = mumble_events.UserStats(self, user)
        self.event_manager.run_callback("Mumble/UserStats", event)

    def send_msg(self, target, message, target_type=None, use_event=True):
        if isinstance(target, int) or isinstance(target, str):
            if target_type == "user":
                target = self.get_user(target)
                if not target:
                    return False
            else:  # Prioritize channels
                target = self.get_channel(target)
                if not target:
                    return False

        if target is None:
            target = self.get_channel()

        if isinstance(target, User):
            self.msg_user(message, target, use_event)
            return True
        elif isinstance(target, Channel):
            self.msg_channel(message, target, use_event)
            return True

        return False

    def send_action(self, target, message, target_type=None, use_event=True):
        if isinstance(target, int) or isinstance(target, str):
            if target_type == "user":
                target = self.get_user(target)
                if not target:
                    return False
            else:  # Prioritize channels
                target = self.get_channel(target)
                if not target:
                    return False

        if target is None:
            target = self.get_channel()

        # TODO: Add italics once formatter is added

        message = u"*%s*" % message
        event = general_events.ActionSent(self, target, message)

        self.event_manager.run_callback("ActionSent", event)

        if isinstance(target, User) and not event.cancelled:
            self.msg_user(message, target, use_event)
            return True
        elif isinstance(target, Channel) and not event.cancelled:
            self.msg_channel(message, target, use_event)
            return True
        return False

    def channel_kick(self, user, channel=None, reason=None, force=False):
        # TODO: Event?
        self.log.debug("Attempting to kick '%s' for '%s'" % (user, reason))
        if not isinstance(user, User):
            user = self.get_user(user)
            if user is None:
                return False
        if not force:
            if not self.ourselves.can_kick(user, channel):
                self.log.trace("Tried to kick, but don't have permission")
                return False
        msg = Mumble_pb2.UserRemove()
        msg.session = user.session
        msg.actor = self.ourselves.session
        if reason is not None:
            msg.reason = reason

        self.sendProtobuf(msg)

    def channel_ban(self, user, channel=None, reason=None, force=False):
        # TODO: Event?
        self.log.debug("Attempting to ban '%s' for '%s'" % (user, reason))
        if not isinstance(user, User):
            user = self.get_user(user)
            if user is None:
                return False
        if not force:
            if not self.ourselves.can_ban(user, channel):
                self.log.trace("Tried to ban, but don't have permission")
                return False
        msg = Mumble_pb2.UserRemove()
        msg.session = user.session
        msg.actor = self.ourselves.session
        if reason is not None:
            msg.reason = reason
        msg.ban = True

        self.sendProtobuf(msg)

    def global_ban(self, user, reason=None, force=False):
        # TODO: Event?
        return False

    def global_kick(self, user, reason=None, force=False):
        # TODO: Event?
        return False

    def msg(self, message, target="channel", target_id=None):
        if target_id is None and target == "channel":
            target_id = self.ourselves.channel.channel_id

        self.log.trace(_("Sending text message: %s") % message)

        if self.use_cgi:
            message = cgi.escape(message)

        msg = Mumble_pb2.TextMessage()  # session, channel_id, tree_id, message
        msg.message = message
        if target == "channel":
            msg.channel_id.append(target_id)
        else:
            msg.session.append(target_id)

        self.sendProtobuf(msg)

    def msg_channel(self, message, channel, use_event=True):
        if isinstance(channel, Channel):
            channel = channel.channel_id

        if use_event:
            event = general_events.MessageSent(self, "message",
                                               self.channels[channel], message)
            self.event_manager.run_callback("MessageSent", event)

            message = event.message

        self.log.info("-> *%s* %s" % (self.channels[channel], message))

        self.msg(message, "channel", channel)

    def msg_user(self, message, user, use_event=True):
        if isinstance(user, User):
            user = user.session

        if use_event:
            event = general_events.MessageSent(self, "message",
                                               self.users[user], message)
            self.event_manager.run_callback("MessageSent", event)

            message = event.message

        self.log.info("-> (%s) %s" % (self.users[user], message))

        self.msg(message, "user", user)

    def join_channel(self, channel, password=None):
        if isinstance(channel, str) or isinstance(channel, unicode):
            channel = self.get_channel(channel)
        if channel is None:
            return False
        if isinstance(channel, Channel):
            channel = channel.channel_id
        msg = Mumble_pb2.UserState()
        msg.channel_id = channel
        self.sendProtobuf(msg)
        return True

    def leave_channel(self, channel=None, reason=None):
        return False

    def request_userstats(self, user, stats_only=False):
        self.log.debug(
            "Requesting UserStats for {}, stats_only={}", user, stats_only
        )
        user_stats = Mumble_pb2.UserStats()
        user_stats.session = user.session
        user_stats.stats_only = stats_only
        self.sendProtobuf(user_stats)

    def get_channel(self, name_or_id=None):
        if name_or_id is None:
            return self.ourselves.channel  # Yay

        if isinstance(name_or_id, str) or isinstance(name_or_id, unicode):
            name = name_or_id.lower()
            for cid, channel in self.channels.iteritems():
                if channel.name.lower() == name:
                    return channel
            return None
        else:
            # Assume ID - it's a hash lookup anyway
            try:
                return self.channels[name_or_id]
            except KeyError:
                return None

    def get_user(self, name_or_session):
        if isinstance(name_or_session, str):
            name = name_or_session.lower()
            for session, user in self.users.iteritems():
                if user.nickname.lower() == name:
                    return user
            return None
        else:
            # Assume session - it's a hash lookup anyway
            try:
                return self.users[name_or_session]
            except KeyError:
                return None

    # region Permissions

    def set_permissions(self, channel, permissions, flush=False):
        # TODO: Investigate flush properly
        self._acls[channel] = permissions

    def has_permission(self, channel, *perms):
        # TODO: Figure out how perms actually work, and how to store them, etc.
        # Note: Do not use these yet.
        if not isinstance(channel, Channel):
            channel = self.get_channel(channel)
        if channel is None or channel not in self._acls:
            return False
        return Perms.has_permission(self._acls[channel], *perms)

    # endregion
