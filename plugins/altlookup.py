# coding=utf-8

from system.decorators import *

class plugin(object):

    """
    This plugin is used to look up a
    Minecraft player's alt accounts using MCBans.
    """

    commands = {
        "alts": "lookup_alts"
    }

    def __init__(self, irc):
        self.irc = irc
        self.help = {
            "alts": "Gets a list of alts for a user\nUsage: %salts <data>\nNOTE: Requires you to be op in the channel of use" % self.irc.control_char
        }

    @config("rank", "op")
    def lookup_alts(self, user, channel, arguments):
        if self.irc.is_op(channel, user):
            if arguments[1:]:
                result = self.irc.mcb.lookupAlts(arguments[1])
                if 'result' in result.keys():
                    self.irc.sendnotice(user, "This plugin requires MCBans premium")
                else:
                    self.irc.sendnotice(user, "Player %s has %s alt accounts" % (arguments[1], result["altListCount"]))
                    if int(result["altListCount"]) > 0:
                        for alt in result["altList"].split(", "):
                            self.irc.sendnotice(user, " - %s" % alt)
            else:
                self.irc.sendnotice(user, "Usage: %salts <data>" % self.irc.control_char)
        else:
            self.irc.sendnotice(user, "You do not have access to this command.")

    hooks = {}

    name = "MCBans alt account lookup"
