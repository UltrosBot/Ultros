# coding=utf-8
import random
from system.yaml_loader import *

from system.decorators import *

class plugin(object):
    """
    Memos memo - This one IS supposed to remind you of something.
    """

    commands = {
        "memo"      : "memo",
        "tell"      : "memo",
        "memoban"   : "ban",
        "memounban" : "unban"
    }

    hooks = {
        "connectionLost": "save",
        "signedOn": "load",
        "privmsg": "privmsg",
        }

    def __init__(self, irc):
        self.irc = irc
        self.memos_handler = yaml_loader(True, "memos")
        self.memos = self.memos_handler.load("memos")
        self.bans_handler = yaml_loader(True, "memos")
        self.bans = self.bans_handler.load("bans")
        if not self.memos:
            self.memos = {}

        if not self.bans:
            self.bans = {"memos": []}

        self.channels = {}
        self.users = {}

        self.help = {
            "memo": "Tells the bot to send a message to the user next time the user says something in the channel.\nUsage: %smemo <user> <message>" % self.irc.control_char
            ,
            "memoban": "Tells the bot to ignore memos from a user.\nUsage: %smemoban <user>\nNOTE: Needs logged into the bot." % self.irc.control_char,
            "memounban": "Tells the bot to stop ignoring memos from a user.\nUsage: %smemounban <user>\nNOTE: Needs to be logged into the bot." %self.irc.control_char
            ,
            }

    def load(self, data=None):
        self.memos = self.memos_handler.load("memos")
        self.bans = self.bans_handler.load("bans")

        if not self.memos:
            self.memos = {}

        if not self.bans:
            self.bans = {"memos": []}

    def save(self, data=None):
        self.memos_handler.save_data("memos", self.memos)
        self.bans_handler.save_data("bans", self.bans)

    def privmsg(self, data):
        user = data['user'].lower()
        channel = data['channel']
        memos = self.memos
        sendto = [key for key in memos]
        if user in sendto:
            memomsg = memos[user]
            message = ', '.join(memomsg)
            self.irc.send_raw("PRIVMSG " + channel + " Memo for " + data['user'] + ": " + message + ".")
            del memos[user]
            self.save()

    def memo(self, user, channel, arguments):
        if len(arguments) > 2:
            msg = '<' + user + "> " + " ".join(arguments[2:])
            receiver = "".join(arguments[1]).lower()
            if user.lower() in self.bans["memos"]:
                self.irc.send_raw("PRIVMSG " + channel + " :\1ACTION is not allowed to get memos from: '" + user + "'.\1")
            elif msg not in self.memos.keys():
                if self.memos.get(receiver) is None:
                    self.memos[receiver] = []
                self.memos[receiver].append(msg)
                self.irc.send_raw(
                    "PRIVMSG " + channel + " I'll send it to " + receiver + ".")
                self.save()
            else:
                self.irc.send_raw(
                    "PRIVMSG " + channel + " :\1ACTION already has this memo on the memolist!\1")
        else:
            self.irc.sendnotice(user, "Usage: %smemo <player> <message>" % self.irc.control_char)

    @config("rank", "authorized")
    def ban(self, user, channel, arguments):
        if len(arguments) == 2:
            ban = " ".join(arguments[1:]).lower()
            self.bans["memos"].append(ban)
            self.save()
            self.irc.sendnotice(user, "User %s banned." %(" ".join(arguments[1:])))
        else:
            self.irc.sendnotice(user, "Usage: %sban <user>" % self.irc.control_char)

    @config("rank", "authorized")
    def unban(self, user, channel, arguments):
        if len(arguments) == 2:
            ban = " ".join(arguments[1:]).lower()
            if ban in self.bans["memos"]:
                self.bans["memos"].remove(ban)
                self.save()
                self.irc.sendnotice(user, "User %s unbanned." %(" ".join(arguments[1:])))
            else:
                self.irc.sendnotice(user, "User %s is not banned." %(" ".join(arguments[1:])))
        else:
            self.irc.sendnotice(user, "Usage: %sunban <user>" % self.irc.control_char)

    name = "Memos"
