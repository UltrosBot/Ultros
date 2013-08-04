# coding=utf-8
class plugin(object):

    """
    This is a roleplay plugin. It's designed to
    make roleplays a little more involved.
    """

    hooks = {}

    name = "Roleplay"

    commands = {
        "rp": "rp"
    }

    def __init__(self, irc):
        self.irc = irc
        self.help = {
            "rp": "Help topic!\nUsage: %srp [command] [args]\nTry %srp help for more info." % (self.irc.control_char, self.irc.control_char)
        }
    
    def rp(self, user, channel, arguments):
        self.irc.sendnotice(user, "Test.")


