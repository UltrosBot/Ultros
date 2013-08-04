import feedparser

from system.yaml_loader import *
from system.decorators import *

class plugin(object):

    """
    Feed parser plugin. Used to notify channels of changes to feeds
    """

    hooks = {}

    name = "Feed parser"

    commands = {
        #        "test": "test"
    }

    def __init__(self, irc):
        self.irc = irc
        self.help = {
            #            "test": "You must be really bored, eh?\nUsage: %stest" % self.irc.control_char
        }

        self.settings_handler = yaml_loader(True, "feeds")
        self.load()

    def load(self):
        self.settings = self.settings_handler.load("settings")
        self.feeds = self.settings_handler.load("feeds")
