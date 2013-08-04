# coding=utf-8
from system.yaml_loader import *
from system.decorators import *

class plugin(object):

    """
    Plugin that removes a user's rank when they change their nick to an away nick
    """

    hooks = {
        "connectionLost": "save",
        "signedOn": "load",
        "userNicked": "nickChanged",
        "userQuit": "userQuit",
        "userParted": "userParted"
    }

    name = "Awaylower"

    commands = {
        "awaynick": "awaynick",
        "awaynicks": "awaynicks"
    }

    def __init__(self, irc):
        self.irc = irc
        self.help = {
                        "awaynick": "Used to manage away nicks for rank dropping.\n"
                                    "Usage: %sawaynick <add|del> nickname" % self.irc.control_char,
                        "awaynicks": "Lists added away nicks for rank dropping.\n"
                                     "Usage: %sawaynicks" % self.irc.control_char
        }

        self.settings_handler = yaml_loader(True, "awaylower")
        self.load()

    @config("rank", "op")
    def awaynick(self, user, channel, arguments):
        if len(arguments) < 3:
            self.irc.sendnotice(user, "Usage: %sawaynick <add|del> nickname" % self.irc.control_char)
        else:
            nicks = self.data["nicks"]
            command = arguments[1]
            nick = arguments[2]
            if command == "add":
                if nick not in self.data["nicks"]:
                    nicks.append(nick)
                    self.data["nicks"] = nicks
                    self.irc.sendnotice(user, "Nick %s has been added to the awaynicks list." % nick)
                    self.save()
                else:
                    self.irc.sendnotice(user, "Nick %s is already in the awaynicks list." % nick)
            elif command == "del":
                if nick in self.data["nicks"]:
                    nicks.remove(nick)
                    self.data["nicks"] = nicks
                    self.irc.sendnotice(user, "Nick %s has been removed from the awaynicks list." % nick)
                    self.save()
                else:
                    self.irc.sendnotice(user, "Nick %s is not in the awaynicks list." % nick)
            else:
                self.irc.sendnotice(user, "Unknown operation \"%s\"" % command)
                self.irc.sendnotice(user, "Usage: %sawaynick <add|remove> nickname" % self.irc.control_char)

    @config("rank", "op")
    def awaynicks(self, user, channel, arguments):
        if len(self.data["nicks"]) > 0:
            self.irc.sendnotice(user, "Listing %s awaynicks:" % len(self.data["nicks"]))
            self.irc.sendnotice(user, ", ".join(self.data["nicks"]))
        else:
            self.irc.sendnotice(user, "There are no awaynicks.")

    def nickChanged(self, data):
        nick = data["nick"]
        oldnick = data["oldnick"]
        if nick in self.data["nicks"]:
            for channel in self.irc.channels:
                dstr = "%s/%s" % (nick, channel)
                statuses = self.irc.getChanStatus(channel, nick)
                self.statuses[dstr] = statuses
                if self.irc.is_op(channel, self.irc.nickname):
                    self.irc.send_raw("MODE %s -hoaq %s %s %s %s" % (channel, nick, nick, nick, nick))
        else:
            for channel in self.irc.channels:
                odstr = "%s/%s" % (oldnick, channel)
                if self.irc.is_op(channel, self.irc.nickname):
                    if odstr in self.statuses:
                        status = self.statuses[odstr]
                        del self.statuses[odstr]
                        if status and len(status) > 0:
                            modes = []
                            if "~" in status:
                                modes.append("q")
                            if "&" in status:
                                modes.append("a")
                            if "@" in status:
                                modes.append("o")
                            if "%" in status:
                                modes.append("h")
                            if len(modes) > 0:
                                nicks = []
                                for x in modes:
                                    nicks.append(nick)
                                self.irc.send_raw("MODE %s +%s %s" % (channel, "".join(modes), " ".join(nicks)))

    def userQuit(self, data):
        for channel in self.irc.channels:
            dstr = "%s/%s" % (data["user"], channel)
            if dstr in self.statuses:
                self.statuses[dstr] = ""

    def userParted(self, data):
        dstr = "%s/%s" % (data["user"], data["channel"])
        if dstr in self.statuses:
            self.statuses[dstr] = ""

    def load(self, data=None):
        self.statuses = {}
        self.data = self.settings_handler.load("data")
        if not self.data:
            self.data = {"nicks": []}
        if not "nicks" in self.data:
            self.data["nicks"] = []
        if not self.data["nicks"]:
            self.data["nicks"] = []

    def save(self, data=None):
        self.settings_handler.save_data("data", self.data)