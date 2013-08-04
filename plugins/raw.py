# coding=utf-8

from system.decorators import *

class plugin(object):

    """
    This plugin is used to send raw
    messages to the server from the bot.
    """

    commands = {
        "raw": "send_raw"
    }

    def __init__(self, irc):
        self.irc = irc
        self.help = {
            "raw": "Send raw data to the IRC server\nUsage: %sraw <data>\nNOTE: Requires you to be logged in" % self.irc.control_char
        }

    @config("rank", "authorized")
    def send_raw(self, user, channel, arguments):
        if user in self.irc.authorized.keys():
            if len(arguments) > 1:
                self.irc.send_raw(" ".join(arguments[1:]))
                self.irc.sendnotice(user, "Done!")
            else:
                self.irc.sendnotice(user, "Usage: %sraw <data>" % self.irc.control_char)
        else:
            self.irc.sendnotice(user, "You do not have access to this command.")

    hooks = {}

    name = "Send raw"
