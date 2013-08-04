# coding=utf-8
class plugin(object):

    """
    This is a test plugin to show exactly how
    the plugin system works. Feel free to use
    this as a base for your other plugins.
    """

    hooks = {}

    name = "Test"

    commands = {
        "test": "test"
    }

    def __init__(self, irc):
        self.irc = irc
        self.help = {
            "test": "You must be really bored, eh?\nUsage: %stest" % self.irc.control_char
        }
    
    def test(self, user, channel, arguments):
        self.irc.sendnotice(user, "Test.")

    def intercom(self, origin, data):
        print "[INTERCOM TEST] %s %s" % (origin, data)
        return "[INTERCOM TEST] IT WORKS!"


