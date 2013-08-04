# coding=utf-8
from system.irc import *
import os

if not os.path.exists("config/settings.yml"):
    print "Couldn't find settings.yml!"
    print "  Copy the settings.yml.example to settings.yml and edit it as required."
    print "  After that, run the bot again."
    exit(1)

factory = BotFactory()  # Create the factory. We could do all setup there, including connection.
# reactor.connectTCP(
#     settings["connection"]["host"],
#     settings["connection"]["port"],
#     factory, 120)
