# coding=utf-8
import random
from system.yaml_loader import *
from twisted.internet import reactor

from system.decorators import *

class plugin(object):
    """
    Random lyrics <3
    """
    
    name = "lyrics"
    
    commands = {
        "sing": "singCommand",
        "reloadlyrics": "loadconfigs",
    }

    hooks = {
        "userJoined": "userJoined"
    }

    
    def __init__(self, irc):
        self.irc = irc
        self.help = {
            "sing": "Sing a song!\nUsage: %ssing" % self.irc.control_char,
            "reloadlyrics": "Reload the lyrics file.\nUsage: %ssing\nNote: You need to be logged in to do this." % self.irc.control_char
        }
        self.loadconfigs()
        self.singing = False

    @config("rank", "authorized")
    def loadconfigs(self, user=False, *args):
        self.settings_handler = yaml_loader(True, "lyrics")
        self.settings = self.settings_handler.load("settings")
        self.lyrics = self.settings_handler.load("lyrics")
        if user: self.irc.send_raw("NOTICE " + user + " :" + 'Lyrics reloaded!')

    def userJoined(self, data):
        #Do I feel like singing? :L
        if random.randint(1, self.settings["possibility"]) == 1:
            self.sing(data["channel"])

    @config("rank", "voice")
    def singCommand(self, user, channel, arguments):
        id = None
        if len(arguments) > 1:
            id = arguments[1]
            try:
                id = int(id)
            except:
                id = None
        self.sing(channel, user, id)
    
    def sing(self, channel, user=None, songID=None):
        if not self.lyrics:
            if user:
                self.irc.sendnotice(user, "I don't know any songs.")
        elif self.singing:
            if user:
                self.irc.sendnotice(user, "I am already singing.")
        elif channel not in self.settings["channels"]:
            if user:
                self.irc.sendnotice(user, "I cannot sing in this channel.")
        else:
            self.singing = True
            try:
                #If no argument was provided, randomly select a song
                if not songID:
                    random.seed()
                    songID = random.randint(1, len(self.lyrics))

                #Get the lyrics
                self.song = self.lyrics[songID]["song"].split("\n")
                if user:
                    self.song.insert(0,"A song just for you, " + user + " <3 (" + self.lyrics[songID]["link"] + ")")

                #Get the delay, and channel
                self.songdelay = self.lyrics[songID]["delay"]
                self.songchan = channel

                #Initialize the variable
                self.line = 0

                #Start singing
                self.singLines(channel)
            except Exception as e:
                if user:
                    self.irc.notice(user, "Error: %s" % e)
                else:
                    self.irc.sendmsg(channel, "Error: %s" % e)
                self.singing = False

    
    def singLines(self, channel):
        if self.line < len(self.song):
            #Print blank lines too
            if self.song[self.line] != '':
                self.irc.send_raw("PRIVMSG " + channel + " :" + self.song[self.line])
            
            self.line += 1
            
            #Delay
            reactor.callLater(self.songdelay, self.singLines, channel)
        else:
            #Song is up!
            self.irc.send_raw("PRIVMSG " + channel + " :" + "\o/")
            self.singing = False
