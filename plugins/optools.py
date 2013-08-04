# coding=utf-8
from system.decorators import *

class plugin(object):

    """
    This plugin contains kick and
    ban commands for op+ users.
    """

    commands = {
        "kick": "kick",
        "ban": "ban"
    }

    def __init__(self, irc):
        self.irc = irc
        self.help = {
            "kick": "Kick a user from a channel\nUsage: %skick <user>[:channel] [reason]\nIf channel is omitted, the current channel is used." % self.irc.control_char,
            "ban": "Kickban a user from a channel\nUsage: %sban <user>[:channel] [reason]\nIf channel is omitted, the current channel is used." % self.irc.control_char
        }

    @config("rank", "op")
    def kick(self, user, channel, arguments):
        if len(arguments) > 1:
            k_user = arguments[1]
            k_chan = channel
            if ":" in k_user:
                k_user, k_chan = k_user.split(":")[0], k_user.split(":")[1]
            k_reason = user
            if len(arguments) > 2:
                k_reason = " ".join(arguments[2:])
            if self.irc.is_op(k_chan, self.irc.nickname):
                if k_user in self.irc.chanlist[channel].keys():
                    self.irc.send_raw("KICK %s %s :%s" % (k_chan, k_user, k_reason))
                    self.irc.sendnotice(user, "User %s kicked from %s." % (k_user, k_chan))
                else:
                    self.irc.sendnotice(user, "User %s is not on %s." % (k_user, k_chan))
            else:
                self.irc.sendnotice(user, "I do not have op on %s" % k_chan)
        else:
            self.irc.sendnotice(user, self.help["kick"])

    @config("rank", "op")
    def ban(self, user, channel, arguments):
        if len(arguments) > 1:
            k_user = arguments[1]
            k_chan = channel
            if ":" in k_user:
                k_user, k_chan = k_user.split(":")[0], k_user.split(":")[1]
            k_reason = user
            if len(arguments) > 2:
                k_reason = " ".join(arguments[2:])
            if self.irc.is_op(k_chan, self.irc.nickname):
                if k_user in self.irc.chanlist[channel].keys():
                    self.irc.send_raw("KICK %s %s :%s" % (k_chan, k_user, k_reason))
                    self.irc.send_raw("MODE %s +b %s" % (k_chan, self.irc.chanlist[channel][k_user]["host"]))
                    self.irc.sendnotice(user, "User %s banned from %s." % (k_user, k_chan))
                else:
                    self.irc.sendnotice(user, "User %s is not on %s." % (k_user, k_chan))
            else:
                self.irc.sendnotice(user, "I do not have op on %s" % k_chan)
        else:
            self.irc.sendnotice(user, self.help["kick"])

    hooks = {}

    name = "Op tools"
