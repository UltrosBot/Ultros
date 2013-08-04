# coding=utf-8
class plugin(object):

    """
    Lastseen plugin: To check when a user was lastseen on IRC, and what they last did.
    """

    hooks = {}

    name = "Lastseen"

    commands = {
        "lastseen": "lastseen"
    }

    def __init__(self, irc):
        self.irc = irc
        self.help = {
            "lastseen": "Check when the bot last saw activity from a user\nUsage: %slastseen <username>" % self.irc.control_char
        }
    
    def lastseen(self, user, channel, arguments):
        self.irc.sendnotice(user, "Test.")


