# coding=utf-8
from system.irc import *
from system.yaml_loader import *
import sys, os

if not os.path.exists("config/settings.yml"):
    print "|! Couldn't find settings.yml!"
    print "|! Copy the settings.yml.example to settings.yml and edit it as required."
    print "|! After that, run the bot again."
    exit(1)

sys.path.append("./depends")

settings = yaml_loader().load("config/settings.yml")
factory = BotFactory()
reactor.connectTCP(
    settings["connection"]["host"],
    settings["connection"]["port"],
    factory, 120)
del settings
colprint("|= Starting up..")
reactor.run()
colprint("0\n")