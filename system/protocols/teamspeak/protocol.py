# coding=utf-8

import utils.teamspeak as utils

from collections import deque
from utils.log import getLogger
from system.decorators import run_async

from twisted.internet import reactor
from system.protocols.generic.protocol import Protocol as GenericProtocol
from threading import Lock


class Protocol(GenericProtocol):

    factory = None
    config = None
    log = None
    event_manger = None

    command_responses = deque()
    command_mutex = Lock()

    receive_mutex = Lock()

    channels = {}
    users = []

    user = ""
    passw = ""
    sid = 1

    def __init__(self, factory, config):
        self.factory = factory
        self.config = config
        self.log = getLogger("TS3")

        self.log.info("Setting up..")

        self.server = config["server"]
        self.identity = config["identity"]

        self.user = self.identity["username"]
        self.passw = self.identity["password"]
        self.sid = self.server["sid"]

        reactor.connectTCP(
            self.server["address"],
            self.server["port"],
            self.factory,
            120
        )

    def shutdown(self):
        self.send_message(2, 0, "Disconnecting: Protocol shutdown")
        self.send_command("quit")
        self.transport.loseConnection()

    def connectionMade(self):
        pass

    def send_command(self, command, args=None, output=True):
        with self.command_mutex:
            if not args:
                args = {}
            done = "%s" % command

            for pair in args.items():
                done = "%s %s=%s" % (done, pair[0], utils.escape(pair[1]))

            if output:  # Check this and debug output if false
                self.log.info("-> %s" % done)
            else:
                self.log.debug("-> %s" % done)

            self.send(done)

            lines = []
            error_line = ""

            while True:
                if not len(self.command_responses):
                    continue

                element = self.command_responses.popleft()
                if element.lower().startswith("error"):
                    error_line = element
                    break
                lines.append(element)

            parsed_lines = []
            for line in lines:
                if "|" in line:  # We've got an array of data
                    chunks = []
                    for chunk in line.split("|"):
                        chunks.append(self.parse_words(chunk.split()))
                    parsed_lines.append(chunks)
                    continue
                parsed_lines.append(self.parse_words(line.split()))
            parsed_error = self.parse_words(error_line.split()[1:])
            done_lines = parsed_lines

            if command.lower().strip() == "clientlist":
                done_lines = parsed_lines
            elif len(parsed_lines) == 1:
                done_lines = parsed_lines[0]

            return {"error_msg": parsed_error["msg"],
                    "error_id": parsed_error["id"],
                    "data": done_lines,
                    "result": True if parsed_error["id"] == "0" else False}

    @run_async
    def send(self, data):
        self.transport.write("%s\n" % data)

    @run_async
    def whoami_heartbeat(self):
        self.send_command("whoami", output=False)
        reactor.callLater(5, self.whoami_heartbeat)

    @run_async
    def do_login(self):
        result = self.send_command("login",
                                   {"client_login_name": self.user,
                                    "client_login_password": self.passw},
                                   output=False)
        if not result["result"]:
            self.log.warn("Unable to login: %s" % result["error_msg"])

        self.log.debug("Selecting server..")
        r = self.send_command("use", {"sid": self.sid}, output=False)

        if not r["result"]:
            self.log.warn("Unable to select server: %s" % r["error_msg"])

        r = self.send_command("clientupdate", {"client_nickname":
                                               self.identity["nickname"]},
                              output=False)

        if not r["result"]:
            self.log.warn("Unable to set nickname: %s"
                          % r["error_msg"])

        self.log.debug("Starting anti-timeout kick heartbeat..")

        self.whoami_heartbeat()

        self.log.debug("Subscribing to events..")

        r = self.send_command("servernotifyregister", {"event": "textserver"},
                              output=False)

        if not r["result"]:
            self.log.warn("Unable to subscribe to server text: %s"
                          % r["error_msg"])

        r = self.send_command("servernotifyregister", {"event": "textchannel"},
                              output=False)

        if not r["result"]:
            self.log.warn("Unable to subscribe to channel text: %s"
                          % r["error_msg"])

        r = self.send_command("servernotifyregister", {"event": "textprivate"},
                              output=False)

        if not r["result"]:
            self.log.warn("Unable to subscribe to private text: %s"
                          % r["error_msg"])

        r = self.send_command("servernotifyregister", {"event": "server"},
                              output=False)

        if not r["result"]:
            self.log.warn("Unable to subscribe server notifications: %s"
                          % r["error_msg"])

        r = self.send_command("whoami", output=False)

        if not r["result"]:
            self.log.warn("Unable to see who I am: %s"
                          % r["error_msg"])
        else:
            cid = r["data"]["client_channel_id"]
            r = self.send_command("servernotifyregister", {"event": "channel",
                                                           "id": cid},
                                  output=False)

            if not r["result"]:
                self.log.warn("Unable to subscribe channel notifications: %s"
                              % r["error_msg"])

        r = self.send_command("whoami")

        if r["result"]:
            self.client_channel_id = r["data"]["client_channel_id"]
            self.client_id = r["data"]["client_id"]

        self.log.info("Logged in.")

        #######################################################################

        self.log.debug("===== CHANNEL LIST =====")

        r = self.send_command("channellist", output=False)

        channel_ids = {}

        for channel in r["data"]:
            channel_ids[channel["cid"]] = channel["channel_name"]
            self.log.debug("> %s: %s (%s clients)"
                           % (channel["cid"], channel["channel_name"],
                              channel["total_clients"]))

        self.log.debug("===== CLIENT LIST =====")

        r = self.send_command("clientlist", output=False)

        self.log.debug(r)

        for client in r["data"][0]:
            self.log.debug("> %s: %s in %s"
                           % (client["clid"], client["client_nickname"],
                              channel_ids[client["cid"]]))

        self.log.info("Ready!")

    def parse_words(self, words):
        done = {}

        for pair in words:
            double = pair.split("=", 1)
            if len(double) != 2:
                continue
            done[double[0]] = utils.unescape(double[1])

        return done

    def handle_notify(self, data):
        words = data.split()
        parsed = self.parse_words(words[1:])
        notify_type = words[0].split("notify")[1]

        invoker = parsed["invokerid"]
        if invoker == self.client_id:
            return

        if notify_type == "textmessage":
            mode = "???"
            if parsed["targetmode"] == "1":
                mode = "PRIVATE"
            elif parsed["targetmode"] == "2":
                mode = "CHANNEL"
            elif parsed["targetmode"] == "3":
                mode = "SERVER "

            self.log.debug("Parsed: %s" % parsed)

            #TODO: Finish testing
            #self.send_message(parsed["targetmode"], parsed["invokerid"],
            #                  "Echo test: %s" % parsed["msg"])

            self.log.info("%s | <%s> %s"
                          % (mode, parsed["invokername"], parsed["msg"]))
        else:
            self.log.debug("Received notification: %s %s"
                           % (notify_type, parsed))

    @run_async
    def do_parse(self, data):
        if data.lower().startswith("ts3"):
            self.log.info("Connected.")
            return
        elif data.lower().startswith("welcome to the"):
            self.log.debug("Welcome message received, setting up..")
            self.do_login()
            return
        elif data.lower().startswith("notify"):
            self.handle_notify(data)
            return

        self.command_responses.append(data)

    def dataReceived(self, data):
        with self.receive_mutex:
            splitdata = data.split("\n\r")
            if "" in splitdata:
                splitdata.remove("")
            for x in splitdata:
                self.log.debug("<- %s" % x)
                self.do_parse(x)

    def send_message(self, mode, target, message):
        _mode = ""

        if str(mode) == "1":
            _mode = "PRIVATE"
        elif str(mode) == "2":
            _mode = "CHANNEL"
            target = self.client_channel_id
        elif str(mode) == "3":
            target = self.sid
            _mode = "SERVER "

        r = self.send_command("sendtextmessage", {"targetmode": mode,
                                                  "target": target,
                                                  "msg": message},
                              output=False)
        if r["result"]:
            self.log.info("%s | -> %s" % (_mode, message))
        else:
            self.log.warn("Unable to send message: %s" % r["error_msg"])
