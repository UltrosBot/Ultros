# coding=utf-8
import os, random, time, math, traceback, sys
import thread, socket, htmlentitydefs
import mechanize
import dns.resolver as resolver

from twisted.internet import reactor, protocol
from twisted.internet.protocol import Factory
from twisted.words.protocols import irc
from colours import *
from system.yaml_loader import yaml_loader

from utils import *

from system.constants import *
from system.decorators import run_async
from system.yaml_loader import *
from system.logging import Logger
from system.intercom import *
from system import faq

from depends.maskchecker import *

class Bot(irc.IRCClient):
    # Extensions the page title parser shouldn't parse
    notParse = ["png", "jpg", "jpeg", "tiff", "bmp", "ico", "gif", "iso", "bin", "pub", "ppk", "doc", "docx", "xls",
                "xlsx", "ppt", "pptx", "svg"]

    # Ignore lists
    ignores = []

    # Settings
    settings = yaml_loader()

    # Plugins!
    plugins = {}
    hooks = {}
    commands = {}

    # Channels
    joinchans = []
    channels = []
    stfuchans = []
    norandom = []

    lookedup = []

    chanlist = {}
    banlist = {}

    firstjoin = 1

    # Message queues
    messagequeue = []
    noticequeue = []
    rawqueue = []

    # Quit quotes
    quotes = []

    # Random emote objects
    emoteobjects = []

    # User system
    authorized = {}
    users = {}
    kicked = []

    # Special IRC chars
    col = "\3" # Colour code
    bold = "\2" # Bold code
    under = "\31" # Underline code
    ital = "\29" # Italics code
    reverse = "\22" # Reverse code
    normal = "\15"# Normalizing code
    ctcp = "\1" # CTCP code

    def receivedMOTD(self, motd):
        for line in motd:
            self.logs.info("MOTD | " + line)

    def parseObjects(self):
        try:
            self.logs.info("Reading in objects from objects.txt...")
            file = open("objects.txt", "r")
            data = file.read()
            self.emoteobjects = data.split("\n")
            self.logs.info("Read %s objects." % len(self.quotes))
        except Exception:
            return False
        else:
            return True

    def parseQuotes(self):
        try:
            self.logs.info("Reading in quit quotes from quotes.txt...")
            file = open("quotes.txt", "r")
            data = file.read()
            self.quotes = data.split("\n")
            self.logs.info("Read %s quotes." % len(self.quotes))
        except:
            return False
        else:
            return True

    def parseSettings(self):
        try:
            self.logs.info(" Reading in settings from settings.yml...")

            self.settings.load("config/settings.yml")

            bot = self.settings["bot"]
            channels = self.settings["channels"]
            other = self.settings["other"]
            connection = self.settings["connection"]
            try:
                rate_limit = self.settings["rate_limit"]
            except:
                self.settings["rate_limit"] = {
                    'message' : {
                        'enable' : True,
                        'lines'  : 5,
                        'time'   : 2.5
                    },
                    'notice' : {
                        'enable' : True,
                        'lines'  : 5,
                        'time'   : 2.5
                    },
                    'raw' : {
                        'enable' : True,
                        'lines'  : 5,
                        'time'   : 2.5
                    }
                }

            oldchans = self.joinchans
            perform = open("perform.txt", "r").readlines()
            for element in perform:
                self.send_raw(element.strip("\n").strip("\r"))
            for element in self.joinchans:
                self.joinchans.remove(element)
            for element in channels:
                self.joinchans.append(element)
                if not element in oldchans and not self.firstjoin == 1:
                    self.send_raw("JOIN %s" % element)
            for element in oldchans:
                if element not in self.joinchans and not self.firstjoin == 1:
                    self.send_raw("PART %s Configuration changed" % element[0])
            if not self.firstjoin == 1:
                self.sendmsg("nickserv", "IDENTIFY %s" % self.settings["nickserv_password"])
            self.loginpass = bot["admin_password"]
            self.control_char = bot["control_character"]
            self.data_dir = bot["data_folder"]
            self.r_emotes = other["emotes"]
            self.use_antispam = other["antispam"]
            self.autokick = other["autokick"]
            self.use_dnsbl = other["use_dnsbl"]
            if connection["use_password"]:
                self.password = connection["password"]
        except Exception:
            return [False, traceback.format_exc()]
        else:
            self.logs.info("Done!")
            return [True, ""]

    @run_async
    def runHook(self, hook, data=None):
        """Used to run hooks for plugins"""
        # print hook, data
        finaldata = []
        if hook in self.hooks.keys():
            for element in self.hooks[hook]:
            #         print element
                if data:
                    value = element[1](data)
                else:
                    value = element[1]()
                if value is not None:
                    finaldata.append(value)
        if finaldata is []:
            finaldata = True
        return {"result": True, "data": finaldata} # Stupid workaround, need to fix

    @run_async
    def loadPlugins(self):
        files = []
        self.hooks = {} # Clear the list of hooks
        self.commands = {} # Clear the list of commands
        for element in os.listdir("plugins"): # List the plugins
            ext = element.split(".")[-1]
            file = element.split(".")[0]
            if element == "__init__.py": # Skip the initialiser
                continue
            elif ext == "py": # Check if it ends in .py
                files.append(file)
        self.logs.info("Loading %s plugins.. " % len(files))
        i = 0
        while i < len(files):
            element = files[i]
            reloaded = False
            if not "plugins.%s" % element in sys.modules.keys(): # Check if we already imported it
                try:
                    __import__("plugins.%s" % element) # If not, import it
                except Exception: # Got an error!
                    self.logs.error("Unable to load plugin from %s.py!" % element)
                    self.logs.error("%s" % traceback.format_exc())
                    i += 1
                    continue
                else:
                    try:
                        mod = sys.modules["plugins.%s" % element].plugin(self)
                        name = mod.name # What's the name?
                        mod.irc = self
                        if hasattr(mod, "gotIRC"):
                            mod.gotIRC()
                        add_plugin(name, mod)
                    except Exception:
                        self.logs.error("Unable to load plugin from %s.py!" % element)
                        self.logs.error("Error: %s" % traceback.format_exc())
                        i += 1
                        continue
            else: # We already imported it
                del self.plugins[element][0]
                del self.plugins[element]
                del sys.modules["plugins.%s" % element] # Unimport it by deleting it
                try:
                    __import__("plugins.%s" % element) # import it again
                except Exception: # Got an error!
                    self.logs.error("Unable to load plugin from %s.py!" % element)
                    self.logs.error("Error: %s" % traceback.format_exc())
                    i += 1
                    continue
                else:
                    try:
                        mod = sys.modules["plugins.%s" % element].plugin(self)
                        name = mod.name # get the name
                        remove_plugin(name)
                        add_plugin(name, mod)
                    except Exception:
                        self.logs.error("Unable to load plugin from %s.py!" % element)
                        self.logs.error("Error: %s" % traceback.format_exc())
                        i += 1
                        del sys.modules["plugins.%s" % filename]
                        continue
                reloaded = True # Remember that we reloaded it
            mod.filename = element
            self.plugins[name] = mod # Put it in the plugins list
            if not reloaded:
                self.logs.info("Loaded plugin: %s" % name)
            else:
                self.logs.info("Reloaded plugin: %s" % name)
            i += 1
        for plugin in self.plugins.values(): # For every plugin,
            if hasattr(plugin, "hooks"):
                for element, fname in plugin.hooks.items(): # For every hook in the plugin,
                    if element not in self.hooks.keys():
                        self.hooks[element] = [] # Make a note of the hook in the hooks dict
                    self.hooks[element].append([plugin, getattr(plugin, fname)])
            if hasattr(plugin, "commands"):
                for element, data in plugin.commands.items():
                    if element in self.commands.keys():
                        self.logs.warn("Command %s is already registered. Overriding." % element)
                    if hasattr(plugin, data):
                        self.commands[element] = getattr(plugin, data)
                    else:
                        self.logs.warn("Plugins '%s' has no function for command '%s'" % (plugin.name, data))
            if hasattr(plugin, "finishedLoading"):
                plugin.finishedLoading()

    def isPluginLoaded(self, name):
        return name in self.plugins.keys()

    def loadPlugin(self, filename):
        for element in self.plugins.keys():
            if filename == self.plugins[element].filename:
                return False
        try:
            __import__("plugins.%s" % filename)
        except Exception: # Got an error!
            self.logs.error("Unable to load plugin from %s.py!" % filename)
            self.logs.error("Error: %s" % traceback.format_exc())
            return False
        else:
            try:
                mod = sys.modules["plugins.%s" % filename].plugin(self)
                name = mod.name # What's the name?
                mod.irc = self
                if hasattr(mod, "gotIRC"):
                    mod.gotIRC()
            except Exception:
                self.logs.error("Unable to load server plugin from %s.py!" % filename)
                self.logs.error("Error: %s" % traceback.format_exc())
                del sys.modules["plugins.%s" % filename]
                return False
            mod.filename = filename
            self.plugins[name] = mod # Put it in the plugins list
            self.logs.info("Loaded plugin: %s" % name)

            if hasattr(mod, "hooks"):
                for element, fname in mod.hooks.items(): # For every hook in the plugin,
                    if element not in self.hooks.keys():
                        self.hooks[element] = [] # Make a note of the hook in the hooks dict
                    self.hooks[element].append([mod, getattr(mod, fname)])
            if hasattr(mod, "commands"):
                for element, data in mod.commands.items():
                    if element in self.commands.keys():
                        self.logs.warn("Command %s is already registered. Overriding." % element)
                    self.commands[element] = getattr(mod, data)

            return True

    def unloadPlugin(self, name):
        if self.isPluginLoaded(name):
            mod = self.plugins[name]
            if hasattr(mod, "hooks"):
                for element, fname in mod.hooks.items(): # For every hook in the plugin,
                    if element in self.hooks.keys():
                        self.hooks[element].remove([mod, getattr(mod, fname)])
            if hasattr(mod, "commands"):
                for element, data in mod.commands.items():
                    if element in self.commands.keys():
                        del self.commands[element]
            if hasattr(self.plugins[name], "pluginUnloaded"):
                self.plugins[name].pluginUnloaded()
            filename = self.plugins[name].filename

            name = mod.name

            del mod
            del self.plugins[name].filename
            del self.plugins[name]
            del sys.modules["plugins.%s" % filename] # Unimport it by deleting it

            self.hooks = {}
            for plugin in self.plugins.values(): # For every plugin,
                if hasattr(plugin, "hooks"):
                    for element, fname in plugin.hooks.items(): # For every hook in the plugin,
                        if element not in self.hooks.keys():
                            self.hooks[element] = [] # Make a note of the hook in the hooks dict
                        self.hooks[element].append([plugin, getattr(plugin, fname)])
                if hasattr(plugin, "commands"):
                    for element, data in plugin.commands.items():
                        if element in self.commands.keys():
                            self.logs.warn("Command %s is already registered. Overriding." % element)
                        self.commands[element] = getattr(plugin, data)

            self.logs.info("Unloaded plugin: %s" % name)

            return True
        return False


    def __init__(self):
        self.logs = Logger()

        stuff = self.parseSettings()

        if not(stuff[0]):
            self.logs.error("Unable to parse settings. Does settings.ini and perform.txt exist?")
            self.logs.error(" Error: %s" % stuff[1])
            reactor.stop()
            exit()
        if not(self.parseQuotes()):
            self.logs.error("Unable to parse quotes.txt. Does it exist? Bot will now quit.")
            reactor.stop()
            exit()
        if not(self.parseObjects()):
            self.logs.error("Unable to parse objects.txt. Does it exist? Bot will now quit.")
            reactor.stop()
            exit()
        self.loadPlugins()
        self.faq = faq.FAQ(self.data_dir, self)
        self.faq.listentries()

    def connectionLost(self, reason):
        # We lost connection. GTFO tiem.
        self.runHook("connectionLost", {"reason": reason})
        self.logs.info("Shutting down!")

    @property
    def nickname(self):
        return self.factory.nickname

    def signedOn(self):
        # OK, we logged on successfully.
        # Log that we signed on.
        self.logs.info("Signed on as %s." % self.nickname)
        # Log in with NickServ.
        self.sendmsg("NickServ", "IDENTIFY %s" % self.settings["bot"]["nickserv_password"])
        #Start the three loops for sending messages and notices and raw lines
        self.messageLoop()
        self.noticeLoop()
        self.rawLoop()
        for element in self.joinchans:
            reactor.callLater(5.0, self.join, ("%s" % element))
        self.runHook("signedOn")

    def joined(self, channel):
        # We joined a channel
        self.logs.info("Joined %s" % channel)
        if not channel in self.chanlist.keys():
            self.chanlist[channel] = {}
        self.channels.append(channel)
        if self.firstjoin == 1:
            self.firstjoin = 0
            # Flush the logfile
        self.who(channel)
        if self.r_emotes:
            reactor.callLater(5, thread.start_new_thread, self.randmsg, (channel,))
        self.runHook("channelJoined", {"channel": channel})

    def randmsg(self, channel):
        if self.r_emotes:
            if channel not in self.norandom:
                messages = [self.ctcp + "ACTION paws at ^ruser^" + self.ctcp, # Oh look, we did need it
                            self.ctcp + "ACTION curls up in ^ruser^'s lap" + self.ctcp,
                            self.ctcp + "ACTION stares at ^ruser^" + self.ctcp,
                            self.ctcp + "ACTION jumps onto the ^robject^" + self.ctcp + "\no3o",
                            self.ctcp + "ACTION rubs around ^ruser^'s leg" + self.ctcp + "\n" + self.ctcp + "ACTION purrs" + self.ctcp
                    ,
                            "Mewl! o3o",
                            "Meow",
                            ":3",
                            "Mreewww.."
                ]
                self.norandom.append(channel)
                random.seed()
                msg = messages[random.randint(0, len(messages) - 1)]
                random.seed()
                if channel in self.chanlist.keys():
                    msg = msg.replace("^ruser^",
                        self.chanlist[channel].keys()[random.randint(0, len(self.chanlist[channel].keys()) - 1)])
                else:
                    msg = msg.replace("^ruser^", "someone")
                random.seed()
                msg = msg.replace("^robject^", self.emoteobjects[random.randint(0, len(self.emoteobjects) - 1)])
                self.sendmsg(channel, msg)
            reactor.callLater(3600, thread.start_new_thread, self.randmsg, (channel,))

    @run_async
    def privmsg(self, user, channel, msg):
        if channel in self.norandom:
            self.norandom.remove(channel)
            # We got a message.
        # Define the userhost
        userhost = user
        user = user.split("!", 1)[0]

        for badperson in self.ignores:
            if checkbanmask(badperson, userhost):
                return

        self.runHook("privmsg", {"user": user, "host": userhost, "channel": channel, "message": msg})

        # Get the username
        send = self.sendnotice
        if channel == self.nickname:
            send = self.sendmsg
            channel = user
        authorized = False
        authtype = 0
        if self.is_op(channel, user) and user in self.authorized.keys():
            authorized = True
            authtype = 3
        elif self.is_op(channel, user):
            authorized = True
            authtype = 1
        elif user in self.authorized.keys():
            authorized = True
            authtype = 2
        if self.use_antispam:
            msg_time = float(time.time())
            if not (authorized or self.is_voice(user, channel)) and channel.startswith("#"):
                difference = msg_time - self.chanlist[channel][user]["last_time"]
                if difference < 0.15:
                    # User is a dirty spammer!
                    if self.is_op(channel, self.nickname):
                        if not user in self.kicked:
                            self.sendLine("KICK %s %s :%s is a dirty spammer!" % (channel, user, user))
                            self.logs.warn("Kicked %s from %s for spamming." % (user, channel))
                            self.kicked.append(user)
                            return

                        else:
                            self.sendLine(
                                "MODE %s +bbb *!%s@* %s!*@* *!*@%s" % (
                                    channel, userhost.split("@")[0].split("!")[1], user, userhost.split("@")[1]))
                            self.sendLine("KICK %s %s :%s is a dirty spammer!" % (channel, user, user))
                            self.logs.warn(" Banned %s from %s for spamming." % (user, channel))
                            return

                if difference > 5.00:
                    if self.is_op(channel, self.nickname):
                        if msg.startswith("#") and len(msg.split(" ")) == 1:
                            # Random channel
                            self.sendLine(
                                "KICK %s %s :Don't do that! ( Did you mean: \"/join %s\"? )" % (channel, user, msg))
                            self.logs.warn("Kicked %s from %s for randomly typing a channel on its own." % (user, channel))
                            self.kicked.append(user)
                            return

        if channel.startswith("#"):
            if channel in self.chanlist.keys():
                if user in self.chanlist[channel].keys():
                    self.chanlist[channel][user]["last_time"] = float(time.time())
        if msg.startswith(self.control_char) or channel == self.nickname:
            command = msg.split(" ")[0].replace(self.control_char, "", 1)
            arguments = msg.split(" ")
            if command == "help":
                if len(arguments) < 2:
                    send(user, "Syntax: %shelp <topic>" % self.control_char)
                    send(user, "Available topics: about, login, logout")
                    if authorized:
                        send(user, "Admin topics: quit, ignore, unignore, listignores")
                    done = []
                    for element in self.plugins.keys():
                        try:
                            for element in self.plugins[element].help.keys():
                                done.append(element)
                        except:
                            self.logs.warn("Plugin %s has no help object!" % element)

                    send(user, ", ".join(sorted(done)))
                else:
                    if arguments[1] == "about":
                        send(user, "I'm the MCBlock.it IRC helper bot.")
                        send(user, "Created by gdude2002, helped by rakiru.")
                        send(user, "I was designed for #mcblockit on irc.freenode.net")
                    elif arguments[1] == "auth":
                        send(user,
                            "Auth is managed with %slogin and %slogout." % (self.control_char, self.control_char))
                        send(user, "If you change your nick, you will be logged out automatically.")
                        send(user, "Channel ops also have some access.")
                    elif arguments[1] == "login":
                        send(user, "Syntax: %slogin <password>" % self.control_char)
                        send(user, "Logs you into the bot using a password set by the bot owner.")
                        send(user, "See %shelp auth for more information." % self.control_char)
                    elif arguments[1] == "logout":
                        send(user, "Syntax: %slogout" % self.control_char)
                        send(user, "Logs you out of the bot, provided you were already logged in.")
                        send(user, "See %shelp auth for more information." % self.control_char)
                    elif arguments[1] == "ping":
                        send(user, "Syntax: %sping <ip>" % self.control_char)
                        send(user, "Retrieves the server information from a Beta/Release server.")
                        send(user, "Can be useful to check if a server is accepting connections.")
                    elif authorized and arguments[1] == "quit":
                        send(user, "Syntax: %squit [message]" % self.control_char)
                        send(user, "Makes the bot quit, with an optional user-defined message. Requires the admin override.")
                        send(user, "If no message is defined, uses a random quote.")
                    elif authorized and arguments[1] == "ignore":
                        send(user, "Syntax: %signore <hostmask>" % self.control_char)
                        send(user, "Adds a hostmask to the ignore list. Requires op+.")
                        send(user, "Any messages from a matching host will be ignored.")
                    elif authorized and arguments[1] == "unignore":
                        send(user, "Syntax: %sunignore <hostmask>" % self.control_char)
                        send(user, "Removes a hostmask from the ignore list. Requires op+.")
                    elif authorized and arguments[1] == "listignores":
                        send(user, "Syntax: %slistignores" % self.control_char)
                        send(user, "Lists the hostmasks in the ignore list. Requires op+.")
                    else:
                        sent = 0
                        for element in self.plugins.keys():
                            try:
                                if arguments[1] in self.plugins[element].help.keys():
                                    helptxt = self.plugins[element].help[arguments[1]]
                                    if "\n" in helptxt:
                                        for element in helptxt.split("\n"):
                                            send(user, element)
                                    else:
                                        send(user, helptxt)
                                    sent = 1
                                    break
                            except:
                                self.logs.warn("Plugin %s has no help object!" % element)
                        if not sent:
                            send(user, "Unknown help topic: %s" % arguments[1])
            elif command == "login":
                if len(arguments) < 2:
                    send(user, "Syntax: %slogin <password>" % self.control_char)
                    send(user, "The password is set by the owner of the bot.")
                else:
                    passw = arguments[1]
                    if passw == self.loginpass:
                        self.authorized[user] = userhost.split("!", 1)[1]
                        send(user, "You have been logged in successfully.")
                        self.logs.info("%s logged in successfully." % user)
                    else:
                        send(user, "Incorrect password! Check for case and spacing!")
                        self.logs.info("%s tried to log in with an invalid password!" % user)
                    return
            elif command == "logout":
                if user in self.authorized.keys():
                    del self.authorized[user]
                    send(user, "You have been logged out successfully.")
                else:
                    send(user,
                        "You were never logged in. Please note that you are logged out automatically when you nick.")
            elif command == "quit":
                if authorized and authtype > 1:
                    if len(arguments) < 2:
                        self.squit()
                    else:
                        self.squit(" ".join(arguments[1:]))
                else:
                    send(user, "You do not have access to this command.")

            elif command == "ping":
                derp = 0
                if len(arguments) > 1:
                    ip = arguments[1]
                    if ":" in ip:
                        server, port = ip.split(":", 1)
                        try:
                            port = int(port)
                        except:
                            if authorized:
                                self.sendmsg(channel, "%s is an invalid port number." % port)
                            else:
                                send(user, "%s is an invalid port number." % port)
                            derp = 1
                    else:
                        server, port = ip, 25565
                    if derp is 0:
                        try:
                            timing = time.time()
                            s = socket.socket()
                            s.settimeout(5.0)
                            s.connect((server, port))
                            ntiming = time.time()
                            elapsed = ntiming - timing
                            msec = math.floor(elapsed * 1000.0)
                            s.send("\xFE")
                            data = s.recv(1)

                            if data.startswith("\xFF"):
                                data = s.recv(255)
                                s.close()
                                data = data[3:]
                                finlist = data.split("\xA7")

                                finished = []

                                for element in finlist:
                                    donestr = ""
                                    for character in element:
                                        if ord(character) in range(128) and not ord(character) == 0:
                                            donestr = donestr + character.encode("LATIN-1", "replace")
                                    finished.append(donestr.strip("\x00"))

                                if authorized:
                                    self.sendmsg(channel, "Server info: %s (%s/%s) [Latency: %smsec]" % (
                                        finished[0], finished[1], finished[2], msec))
                                else:
                                    send(user, "Server info: %s (%s/%s) [Latency: %smsec]" % (
                                        finished[0], finished[1], finished[2], msec))
                            else:
                                if authorized:
                                    self.sendmsg(channel,
                                        "That doesn't appear to be a Minecraft server. [Latency: %smsec]" % msec)
                                else:
                                    send(user, "That doesn't appear to be a Minecraft server. [Latency: %smsec]" % msec)
                        except Exception:
                            error = str(traceback.format_exc()).split("\n")
                            if '' in error:
                                error.remove('')
                            if ' ' in error:
                                error.remove(' ')
                            error = error[-1]
                            if authorized:
                                self.sendmsg(channel, error)
                            else:
                                send(user, error)
            elif command == "ignore":
                if authorized:
                    if len(arguments) > 1:
                        hostmask = arguments[1]
                        if ("!" in hostmask) and ("@" in hostmask):
                            if not hostmask in self.ignores:
                                self.ignores.append(hostmask)
                                send(user, "Hostmask added to the ignore list: %s" % hostmask)
                            else:
                                send(user, "Hostmask already in the ignore list: %s" % hostmask)
                        else:
                            send(user, "The hostmask must contain a '!' and a '@'!")
                    else:
                        send(user, "Syntax: %signore <hostmask>" % self.control_char)
                else:
                    send(user, "You do not have access to this command.")
            elif command == "unignore":
                if authorized:
                    if len(arguments) > 1:
                        hostmask = arguments[1]
                        if ("!" in hostmask) and ("@" in hostmask):
                            if hostmask in self.ignores:
                                self.ignores.remove(hostmask)
                                send(user, "Hostmask removed from the ignore list: %s" % hostmask)
                            else:
                                send(user, "Hostmask not in the ignore list: %s" % hostmask)
                        else:
                            send(user, "The hostmask must contain a '!' and a '@'!")
                    else:
                        send(user, "Syntax: %sunignore <hostmask>" % self.control_char)
                else:
                    send(user, "You do not have access to this command.")
            elif command == "listignores":
                if authorized:
                    if len(self.ignores) > 0:
                        ary = []
                        for element in self.ignores:
                            ary.append(element)
                            if len(ary) > 9:
                                self.sendnotice(user, ", ".join(ary))
                                ary = []
                        if len(ary) > 0:
                            self.sendnotice(user, ", ".join(ary))
                    else:
                        self.sendnotice(user, "There are no ignores.")
                else:
                    send(user, "You do not have access to this command.")
            elif command.lower() in self.commands.keys():
                try:
                    self.runcommand(command.lower(), user, channel, arguments)
                except Exception as e:
                    traceback.print_exc(e)
                    send(user, "Error: %s" % e)
            else:
                self.logs.info("DEBUG: No such command")
        elif msg.startswith("??") or msg.startswith("?!"):
            cinfo = {"user": user, "hostmask": userhost.split("!", 1)[1], "origin": channel, "message": msg,
                     "target": channel}
            parts = msg.split(" ")
            if len(parts) > 1:
                if parts[0] == "??": # Check in channel
                    if len(parts) > 1:
                        data = self.faq.get(parts[1].lower(), cinfo)
                        if data[0]:
                            for element in data[1]:
                                if not element.strip() == "":
                                    if "\n" in element:
                                        for part in element.split("\n"):
                                            self.sendmsg(channel, "(%s) %s" % (parts[1].lower(), part))
                                    else:
                                        self.sendmsg(channel, "(%s) %s" % (parts[1].lower(), element))
                        else:
                            if data[1] is ERR_NO_SUCH_ENTRY:
                                send(user, "No such entry: %s" % parts[1].lower())
                            else:
                                send(user, "Unable to load entry: %s" % parts[1].lower())
                    else:
                        send(user, "Please provide a help topic. For example: ?? help")
                elif parts[0] == "?!": # Check in channel without eval
                    if len(parts) > 1:
                        data = self.faq.get_noeval(parts[1].lower(), cinfo)
                        if data[0]:
                            for element in data[1]:
                                if not element.strip() == "":
                                    self.sendmsg(channel, "(%s) %s" % (parts[1].lower(), element))
                        else:
                            if data[1] is ERR_NO_SUCH_ENTRY:
                                send(user, "No such entry: %s" % parts[1].lower())
                            else:
                                send(user, "Unable to load entry: %s" % parts[1].lower())
                    else:
                        send(user, "Please provide a help topic. For example: ?! help")
                elif parts[0] == "??>": # Check in channel with target
                    if len(parts) > 2:
                        cinfo = {"user": user, "hostmask": userhost.split("!", 1)[1], "origin": channel, "message": msg,
                                 "target": parts[1]}
                        data = self.faq.get(parts[2].lower(), cinfo)
                        if data[0]:
                            for element in data[1]:
                                if not element.strip() == "":
                                    if "\n" in element:
                                        for part in element.split("\n"):
                                            self.sendmsg(channel, "%s: (%s) %s" % (parts[1], parts[2].lower(), part))
                                else:
                                    self.sendmsg(channel, "%s: (%s) %s" % (parts[1], parts[2].lower(), element))
                        else:
                            if data[1] is ERR_NO_SUCH_ENTRY:
                                send(user, "No such entry: %s" % parts[2].lower())
                            else:
                                send(user, "Unable to load entry: %s" % parts[2].lower())
                    else:
                        send(user, "Please provide a help topic and target user. For example: ??> helpme help")
                elif parts[0] == "??>>": # Check in message to target
                    if len(parts) > 2:
                        cinfo = {"user": user, "hostmask": userhost.split("!", 1)[1], "origin": channel, "message": msg,
                                 "target": parts[1]}
                        data = self.faq.get(parts[2].lower(), cinfo)
                        if data[0]:
                            for element in data[1]:
                                if not element.strip() == "":
                                    if "\n" in element:
                                        for part in element.split("\n"):
                                            self.sendmsg(parts[1], "(%s) %s" % (parts[2].lower(), part))
                                    else:
                                        self.sendmsg(parts[1], "(%s) %s" % (parts[2].lower(), element))
                            send(user, "Topic '%s' has been sent to %s." % (parts[2].lower(), parts[1]))
                        else:
                            if data[1] is ERR_NO_SUCH_ENTRY:
                                send(user, "No such entry: %s" % parts[2].lower())
                            else:
                                send(user, "Unable to load entry: %s" % parts[2].lower())
                    else:
                        send(user, "Please provide a help topic and target user. For example: ??>> helpme help")
                elif parts[0] == "??<": # Check in message to self
                    if len(parts) > 1:
                        cinfo = {"user": user, "hostmask": userhost.split("!", 1)[1], "origin": channel, "message": msg,
                                 "target": user}
                        data = self.faq.get(parts[1].lower(), cinfo)
                        if data[0]:
                            for element in data[1]:
                                if not element.strip() == "":
                                    if "\n" in element:
                                        for part in element.split("\n"):
                                            send(user, "(%s) %s" % (parts[1].lower(), part))
                                    else:
                                        send(user, "(%s) %s" % (parts[1].lower(), element))
                        else:
                            if data[1] is ERR_NO_SUCH_ENTRY:
                                send(user, "No such entry: %s" % parts[1].lower())
                            else:
                                send(user, "Unable to load entry: %s" % parts[1].lower())
                    else:
                        send(user, "Please provide a help topic. For example: ??< help")
                elif parts[0] == "??+": # Add or append to a topic
                    if authorized:
                        if len(parts) > 2:
                            data = self.faq.set(parts[1].lower(), " ".join(parts[2:]), MODE_APPEND)
                            self.faq.listentries()
                            if data[0]:
                                send(user, "Successfully added to the topic: %s" % parts[1].lower())
                            else:
                                send(user, "Unable to add to the topic: %s" % parts[1].lower())
                                if data[1] is ERR_NO_SUCH_ENTRY:
                                    send(user, "Entry does not exist.")
                                else:
                                    send(user, "Please report this to the MCBlock.it staff.")
                        else:
                            send(user,
                                "Please provide a help topic and some data to append. For example: ??+ help This is what you do..")
                    else:
                        send(user, "You do not have access to this command.")
                elif parts[0] == "??~": # Add or replace topic
                    if authorized:
                        if len(parts) > 2:
                            data = self.faq.set(parts[1].lower(), " ".join(parts[2:]), MODE_REPLACE)
                            self.faq.listentries()
                            if data[0]:
                                send(user, "Successfully replaced topic: %s" % parts[1].lower())
                            else:
                                send(user, "Unable to replace the topic: %s" % parts[1].lower())
                                if data[1] is ERR_NO_SUCH_ENTRY:
                                    send(user, "Entry does not exist.")
                                else:
                                    send(user, "Please report this to the MCBlock.it staff.")
                        else:
                            send(user,
                                "Please provide a help topic and some data to use. For example: ??~ help This is what you do..")
                    else:
                        send(user, "You do not have access to this command.")
                elif parts[0] == "??-": # Remove topic
                    if authorized:
                        if len(parts) > 1:
                            data = self.faq.set(parts[1].lower(), '', MODE_REMOVE)
                            self.faq.listentries()
                            if data[0]:
                                send(user, "Successfully removed the topic: %s" % parts[1].lower())
                            else:
                                send(user, "Unable to remove the topic: %s" % parts[1].lower())
                                if data[1] is ERR_NO_SUCH_ENTRY:
                                    send(user, "Entry does not exist.")
                                else:
                                    send(user, "Please report this to the MCBlock.it staff.")
                        else:
                            send(user, "Please provide a help topic to remove. For example: ??- help")
                    else:
                        send(user, "You do not have access to this command.")
                        # Flush the logfile
        # Log the message
        if channel.startswith("#"):
            self.logs.ircPublic(user, channel, msg)
        else:
            self.logs.ircPrivate(user, msg)

    ranknums = {"none": 0, "voice": 15, "halfop": 30, "op": 45, "admin": 60, "owner": 85, "oper": 100,
                "authorized": 200}

    def who(self, target):
        """Send a WHO request to the server."""
        self.send_raw('WHO %s' % target)

    def runcommand(self, command, user, channel, arguments):
        if command in self.commands.keys():
            command_func = self.commands[command]
            if hasattr(command_func, "config"):
                if "rank" in command_func.config.keys():
                    user_rank = self.getRank(channel, user)
                    needed_rank = command_func.config["rank"]
                    if isinstance(needed_rank, int):
                        if needed_rank > self.ranknums[user_rank]:
                            self.sendnotice(user, "You do not have access to that command")
                        else:
                            command_func(user, channel, arguments)
                    else:
                        if needed_rank in self.ranknums.keys():
                            if self.ranknums[needed_rank] > self.ranknums[user_rank]:
                                self.sendnotice(user, "You do not have access to that command")
                            else:
                                command_func(user, channel, arguments)
                        else:
                            self.logs.warn("Rank %s is not a valid rank!" % needed_rank)
                            command_func(user, channel, arguments)
            else:
                command_func(user, channel, arguments)
        else:
            self.logs.warn("Command %s does not exist" % command)
            self.sendnotice(user, "Command %s does not exist!" % command)

    @run_async
    def dnslookup(self, channel, user):
        """
        Looks up users on several DNS blacklists and kicks them if the bot is op
        This is currently not implemented because it'll lag heavily

        THIS IS NOW BEING TESTED - PLEASE DO NOT ENABLE IT YET
        """
        if self.use_dnsbl and self.is_op(channel, self.nickname):
            ip = socket.gethostbyname(self.chanlist[channel][user]["host"])
            if not ip in self.lookedup:
                r_ip = ip.split(".")
                r_ip.reverse()
                r_ip = ".".join(r_ip)
                blacklists = ["dnsbl.ahbl.org", "ircbl.ahbl.org", "rbl.efnet.org", "dnsbl.dronebl.org",
                              "dnsbl.mcblacklist.com"]
                for bl in blacklists:
                    self.logs.info("Checking user %s on blacklist %s..." % (user, bl))
                    try:
                        resolver.query(r_ip + "." + bl, "A")
                    except resolver.NXDOMAIN:
                        self.logs.info("User %s is clean." % user)
                        pass
                    except Exception as e:
                        self.logs.error("Error looking up user %s: %s" % (user, e))
                    else:
                        self.logs.warn("User %s is blacklisted!" % user)
                        try:
                            answer = resolver.query(r_ip + "." + bl, "TXT")
                            reason = answer[0]
                        except:
                            reason = bl
                        self.sendLine("KICK %s %s :%s" % (channel, user, reason))
                        self.sendLine("MODE %s +b %s" % ip)
                self.lookedup.append(ip)

    def squit(self, reason=""):
        if not reason == "":
            self.sendLine("QUIT :" + reason)
        else:
            random.seed()
            quitmsg = self.quotes[random.randint(0, len(self.quotes) - 1)].strip("\r")
            self.sendLine("QUIT :%s" % quitmsg)
        self.logs.warn("QUITTING!")

    def left(self, channel):
        # We left a channel.
        self.logs.info("Left %s" % channel)
        # Flush the logfile
        self.runHook("channelLeft", channel)

    @run_async
    def ctcpQuery(self, user, me, messages):
        name = user.split("!", 1)[0]
        # It's a CTCP query!
        if messages[0][0].lower() == "action":
            actions = {"pets": self.ctcp + "ACTION purrs" + self.ctcp,
                       "strokes": self.ctcp + "ACTION purrs" + self.ctcp,
                       "feeds": self.ctcp + "ACTION noms ^user^'s food" + self.ctcp + "\n=^.^="
            }
            for element in actions.keys():
                action = element + " " + self.nickname
                act = action.lower().strip()
                if messages[0][1].lower().strip() == act:
                    message = actions[element]
                    message = message.replace("^user^", user.split("!")[0])
                    message = message.replace("^hostmask^", user.split("!")[1])
                    message = message.replace("^host^", user.split("@")[1])
                    message = message.replace("^me^", me)
                    self.sendmsg(me, message)
        elif messages[0][0].lower() == "version":
            self.ctcpMakeReply(name, [(messages[0][0], "A Python bot written for #mcblockit. See .help about")])
            self.logs.info("<- %s [CTCP VERSION]" % user)
            self.logs.info("-> %s [CTCP VERSION REPLY] A Python bot written for #mcblockit. See .help about" % user)
        elif messages[0][0].lower() == "finger":
            self.ctcpMakeReply(name, [(messages[0][0], "No. Just, no.")])
            self.logs.info("<- %s [CTCP FINGER]" % user)
            self.logs.info("-> %s [CTCP FINGER REPLY] No. Just, no." % user)
        else:
            self.logs.info("<- %s [CTCP %s] %s" % (user, messages[0][0].upper(), " ".join(messages[0])))

        self.runHook("ctcpQuery", {"user": name, "host": user.split("!", 1)[1], "target": me, "type": messages[0][0],
                                   "message": messages[0][1]})

    def checkban(self, channel, banmask, owner):
        if self.autokick and self.is_op(channel, self.nickname):
            for element in self.chanlist[channel].keys():
                hostmask = self.chanlist[channel][element]["hostmask"]
                user = element
                if not self.is_op(channel, user) or self.is_voice(channel, user):
                    if checkbanmask(banmask, hostmask):
                        self.send_raw("KICK %s %s :Matched ban mask %s by %s" % (channel, user, banmask, owner))


    def modeChanged(self, user, channel, set, modes, args):
        # Mode change.
        userhost = user
        user = user.split("!", 1)[0]
        if isinstance(args, list):
            self.logs.ircModesSet(channel, user, modes, " ".join(args), set)
        else:
            self.logs.ircModesSet(channel, user, modes, args, set)
        self.runHook("modechanged", {"user": user, "host": userhost, "channel": channel, "set": set, "modes": modes,
                                     "args": args})
        try:
            if set:
                i = 0
                for element in modes:
                    if element in ["q", "a", "o", "h", "v"]:
                        arg = args[i]
                        if "!" not in arg or "@" not in arg:
                            if arg in self.chanlist[channel].keys():
                                mchar = ""
                                if element == "q":
                                    mchar = "~"
                                elif element == "a":
                                    mchar = "&"
                                elif element == "o":
                                    mchar = "@"
                                elif element == "h":
                                    mchar = "%"
                                elif element == "v":
                                    mchar = "+"
                                if not mchar in self.chanlist[channel][arg]["status"]:
                                    self.chanlist[channel][arg]["status"] += mchar
                                print self.chanlist[channel][arg]
                    elif element == "b":
                        if self.is_op(channel, self.nickname):
                            if args[i] == "*!*@*":
                                self.send_raw("KICK %s %s :Do not set such ambiguous bans!" % (channel, user))
                                self.send_raw("MODE %s -b *!*@*" % channel)
                                self.send_raw("MODE %s +b *!*@%s" % (channel, userhost.split("@")[1]))
                            else:
                                self.checkban(channel, args[i], user)
                            #if args[i].lower() == self.nickname.lower():
                        #    for element in self.chanlist[channel].keys():
                    #        self.dnslookup(channel, element)
                    i += 1
            else:
                i = 0
                for element in modes:
                    if element in "qaohv":
                        arg = args[i]
                        if "!" not in arg or "@" not in arg:
                            if arg in self.chanlist[channel].keys():
                                mchar = ""
                                if element == "q":
                                    mchar = "~"
                                elif element == "a":
                                    mchar = "&"
                                elif element == "o":
                                    mchar = "@"
                                elif element == "h":
                                    mchar = "%"
                                elif element == "v":
                                    mchar = "+"
                                if mchar in self.chanlist[channel][arg]["status"]:
                                    self.chanlist[channel][arg]["status"] = self.chanlist[channel][arg]["status"].replace(mchar, "")
                                print self.chanlist[channel][arg]
                    i += 1
        except:
            pass
            # Flush the logfile

    def kickedFrom(self, channel, kicker, message):
        self.runHook("kickedBot", {"channel": channel, "kicker": kicker, "message": message})
        # Onoes, we got kicked!
        self.logs.info("Kicked from %s by %s: %s" % (channel, kicker, message))
        # Flush the logfile

    def nickChanged(self, nick):
        self.runHook("nickedBot", {"oldnick": self.nickname, "newnick": nick})
        # Some evil muu changed MY nick!
        self.logs.info("Nick changed to %s" % nick)
        self.factory.nickname = nick
        # Flush the logfile

    def userJoined(self, user, channel):
        self.runHook("userJoined", {"user": user, "channel": channel})
        self.who(channel)
        self.dnslookup(channel, user)
        # Ohai, welcome to mah channel!
        self.logs.info("%s joined %s" % (user, channel))
        # Flush the logfile

    def userLeft(self, user, channel):
        self.runHook("userParted", {"user": user, "channel": channel})
        # Onoes, bai!
        self.logs.info("%s left %s" % ((user.split("!")[0]), channel))
        # Flush the logfile

    def userKicked(self, kickee, channel, kicker, message):
        # Mwahahaha, someone got kicked!
        kickee = kickee.split("!", 1)[0]
        kicker = kicker.split("!", 1)[0]

        if kickee in self.chanlist[channel].keys():
            del self.chanlist[channel][kickee]

        self.runHook("userKicked", {"kickee": kickee, "kicker": kicker, "channel": channel, "message": message})
        self.logs.info("%s was kicked from %s by %s [%s]" % (kickee, channel, kicker, message))
        # Flush the logfile

    def irc_QUIT(self, user, params):
        # Someone quit.
        userhost = user.split('!')[1]
        user = user.split('!')[0]
        quitMessage = params[0]
        for element in self.chanlist.keys():
            if user in self.chanlist[element].keys():
                del self.chanlist[element][user]
        self.runHook("userQuit", {"user": user, "host": userhost, "message": quitMessage})
        self.logs.info("%s has left irc: %s" % (user, quitMessage))
        # Flush the logfile

    def topicUpdated(self, user, channel, newTopic):
        # Topic was changed. Also called on a channel join.
        userhost = user
        user = user.split("!")[0]
        self.runHook("topicChanged", {"user": user, "host": userhost, "topic": newTopic, "channel": channel})
        self.logs.info("%s set topic %s to \"%s%s15\"" % (user, channel, newTopic, self.col))
        # Flush the logfile

    def irc_NICK(self, prefix, params):
        # Someone changed their nick.
        oldnick = prefix.split("!", 1)[0]
        newnick = params[0]
        self.logs.info("%s is now known as %s" % (oldnick, newnick))
        if oldnick in self.authorized.keys():
            self.sendnotice(newnick,
                "You have been logged out for security reasons. This happens automatically when you change your nick.")
            del self.authorized[oldnick]
        for element in self.chanlist.keys():
            if oldnick in self.chanlist[element].keys():
                self.chanlist[element][newnick] = self.chanlist[element][oldnick]
                del self.chanlist[element][oldnick]
                # Flush the logfile
        self.runHook("userNicked", {"oldnick": oldnick, "nick": newnick})

    def messageLoop(self, wut=None):
        self.m_protect = 0
        while self.m_protect < self.settings['rate_limit']['message']['lines']:
            user = ""
            message = ""
            try:
                item = self.messagequeue.pop(0).split(":", 1)
                user = item[0]
                message = item[1]
                self.sendmessage(user, message)
            except IndexError:
                break
            except Exception:
                try:
                    self.logs.error("Failed to send message! Error: %s" % traceback.format_exc())
                    self.logs.error(user + " -> " + message)
                except:
                    pass
            self.m_protect += 1
        reactor.callLater(self.settings['rate_limit']['message']['time'], self.messageLoop, ())

    def rawLoop(self, wut=None):
        self.r_protect = 0
        while self.r_protect < self.settings['rate_limit']['raw']['lines']:
            item = ""
            try:
                item = self.rawqueue.pop(0)
                self.send_raw_direct(item)
            except IndexError:
                break
            except Exception:
                try:
                    self.logs.error("Failed to send raw data to server! Error: %s" % traceback.format_exc())
                    self.logs.error(item)
                except:
                    pass
            self.r_protect += 1
        reactor.callLater(self.settings['rate_limit']['raw']['time'], self.rawLoop, ())

    def noticeLoop(self, wut=None):
        self.n_protect = 0
        while self.n_protect < self.settings['rate_limit']['notice']['lines']:
            user = ""
            message = ""
            try:
                item = self.noticequeue.pop(0).split(":", 1)
                user = item[0]
                message = item[1]
                self.sendntc(user, message)
            except IndexError:
                break
            except Exception:
                try:
                    self.logs.error("Failed to send notice! Error: %s" % traceback.format_exc())
                    self.logs.error(user + " -> " + message)
                except:
                    pass
            self.n_protect += 1
        reactor.callLater(self.settings['rate_limit']['notice']['time'], self.noticeLoop, ())

    def irc_RPL_WHOREPLY(self, *nargs):
        """Receive WHO reply from server"""
        # ('apocalypse.esper.net', ['McPlusPlus_Testing', '#minecraft', 'die', 'inafire.com', 'apocalypse.esper.net', 'xales|gone', 'G*', '0 xales'])

        data = nargs[1]

        channel = data[1]
        ident = data[2] # Starts with a ~ if there's no identd present
        host = data[3]
        server = data[4]
        nick = data[5]
        status = data[6].strip("G").strip("H").strip("*")
        gecos = data[7] # Hops, realname

        hostmask = nick + "!" + ident + "@" + host

        if not nick in self.chanlist[channel].keys():
            self.chanlist[channel][nick] = {}

        self.chanlist[channel][nick]["ident"] = ident
        self.chanlist[channel][nick]["host"] = host
        self.chanlist[channel][nick]["hostmask"] = hostmask
        self.chanlist[channel][nick]["realname"] = gecos.split(" ")[1]
        self.chanlist[channel][nick]["server"] = server

        if not "status" in self.chanlist[channel][nick].keys():
            self.chanlist[channel][nick]["status"] = status

    def irc_RPL_ENDOFWHO(self, *nargs):
        """Called when WHO output is complete"""
        # ('eldridge.esper.net', ['McPlusPlus_Testing', '#mc++', 'End of /WHO list.'])
        data = nargs[1]
        channel = data[1]

        self.send_raw("MODE %s b" % channel)

    def irc_unknown(self, prefix, command, params):
        """Handle packets that aren't handled by the library."""

        if command == "RPL_BANLIST":
            channel = params[1]
            mask = params[2]
            owner = params[3]
            btime = params[4]

            if channel not in self.banlist.keys():
                done = {"done": False, "total": 1}
                banmask = {"owner": owner.split("!")[0], "ownerhost": owner, "time": btime, "mask": mask,
                           "channel": channel}
                done[mask] = banmask
                self.banlist[channel] = done

            else:
                if not self.banlist[channel]["done"]:
                    banmask = {"owner": owner.split("!")[0], "ownerhost": owner, "time": btime, "mask": mask,
                               "channel": channel}
                    self.banlist[channel][mask] = banmask
                    self.banlist[channel]["total"] += 1

                else:
                    done = {"done": False, "total": 1}
                    banmask = {"owner": owner.split("!")[0], "ownerhost": owner, "time": btime, "mask": mask,
                               "channel": channel}
                    done[mask] = banmask
                    self.banlist[channel] = done

        elif command == "RPL_ENDOFBANLIST":
            channel = params[1]

            if channel in self.banlist.keys():
                self.banlist[channel]["done"] = True
            else:
                self.banlist[channel] = {"done": True, "total": 0}

            if self.is_op(channel, self.nickname):
                stuff = self.banlist[channel].keys()
                stuff.remove("done")
                stuff.remove("total")

                for element in stuff:
                    if stuff == "*!*@*":
                        self.send_raw("KICK %s %s :Do not set such ambiguous bans!" % (
                            channel, self.banlist[channel][element]["owner"]))
                        self.send_raw("MODE %s -b *!*@*" % channel)
                        self.send_raw(
                            "MODE %s +b *!*@%s" % (channel, self.banlist[channel][element]["ownerhost"].split("@")[1]))
                    else:
                        self.checkban(channel, element, self.banlist[channel][element]["owner"])

            self.logs.info("Got %s bans for %s." % (self.banlist[channel]["total"], channel))

        elif command == "RPL_NAMREPLY":
            me, status, channel, names = params
            users = names.split()
            ranks = "+%@&~"

            if not channel in self.chanlist.keys():
                self.chanlist[channel] = {}

            for element in users:
                rank = ""

                for part in ranks:
                    if part in element:
                        rank = rank + part
                    element = element.strip(part)

                if not element in self.chanlist[channel].keys():
                    self.chanlist[channel][element] = {}

                self.chanlist[channel][element]["server"] = prefix
                self.chanlist[channel][element]["status"] = rank
                self.chanlist[channel][element]["last_time"] = float( time.time() - 0.25 )

            self.logs.info("Names for %s: %s" % (channel, names))
            if status == "@":
                self.logs.info("%s is a secret channel." % channel)
            elif status == "*":
                self.logs.info("%s is a private channel." % channel)
            else:
                self.logs.info("%s is a public channel." % channel)

        elif command == "RPL_ENDOFNAMES":
            me, channel, message = params
            ops = 0
            voices = 0
            opers = 0
            aways = 0

            for element in self.chanlist[channel].values():
                status = element["status"]
                if "+" in status:
                    voices += 1
                if "@" in status:
                    ops += 1
                if "*" in status:
                    opers += 1
                if "G" in status:
                    aways += 1
            self.logs.info("%s users on %s (%s voices, %s ops, %s opers, %s away)" % (
            len(self.chanlist[channel]), channel, voices, ops, opers, aways))
        elif str(command) == "972":
            self.logs.error("Unable to kick user: " + params[2])
        elif str(command) in ["265", "266"]:
            self.logs.info("INFO | " + params[1])
        elif not command == "PONG":
            self.logs.info("[%s] (%s) %s" % (prefix, command, params))

        self.runHook("unknownMessage", {"prefix": prefix, "command": command, "params": params})

    #-#################################-#
    #                                   #
    #       UTILITY   #   FUNCTIONS     #
    #                                   #
    #-#################################-#

    def getChanStatus(self, channel, user):
        """
        Returns the status string for a user on a specific channel.
        Returns the empty string if no status was found.
        """

        if channel in self.chanlist and user in self.chanlist[channel] and "status" in self.chanlist[channel][user]:
            return self.chanlist[channel][user]["status"]
        else:
            return ""

    def getRank(self, channel, user):
        """
        This function is for getting the highest rank of a user on any particular channel.
        It will also return "authorized" if the user is logged in or "none" if they don't have a rank.
        """
        # H - not away, G - away, * - IRCop, ~ - owner, & - admin, @ - op, % - halfop, + - voice
        if user in self.authorized.keys():
            return "authorized"

        elif channel in self.chanlist.keys() and user in self.chanlist[channel].keys() and "status" in self.chanlist[channel][user].keys():

            status = self.chanlist[channel][user]["status"]

            if "*" in status:
                return "oper"
            elif "~" in status:
                return "owner"
            elif "&" in status:
                return "admin"
            elif "@" in status:
                return "op"
            elif "%" in status:
                return "halfop"
            elif "+" in status:
                return "voice"
            else:
                return "none"
        else:
            return "none"

    def is_op(self, channel, user):
        return self.getRank(channel, user) in ["op", "admin", "owner", "oper", "authorized"]

    def is_voice(self, channel, user):
        return self.getRank(channel, user) in ["voice", "halfop", "op", "admin", "owner", "oper", "authorized"]

    def cmsg(self, message):
        # Send a message to all joined channels
        for element in self.joinchans:
            self.sendmsg("#" + element[0], message.encode('LATIN-1', 'replace'))

    def cnotice(self, message):
        # Notice all channels
        for element in self.joinchans:
            self.sendnotice("#" + element[0], message.encode('LATIN-1', 'replace'))

    def unescape_charref(self, ref):
        name = ref[2:-1]
        base = 10
        if name.startswith("x"):
            name = name[1:]
            base = 16
        return unichr(int(name, base))

    def replace_entities(self, match):
        ent = match.group()
        if ent[1] == "#":
            return self.unescape_charref(ent)

        repl = htmlentitydefs.name2codepoint.get(ent[1:-1])
        if repl is not None:
            repl = unichr(repl)
        else:
            repl = ent
        return repl

    def unescape(self, data):
        return re.sub(r"&#?[A-Za-z0-9]+?;", self.replace_entities, data)

    # Don't use this directy, use send_raw
    def send_raw_direct(self, line):
        self.sendLine(line)
        self.logs.ircSendMessage("[SERVER]", line)

    # Don't use this directy, use sendmsg
    def sendmessage(self, user, message):
        #TODO: Better max-length check
        if len(message) > 300:
            message = message[:300] + "..."
        if user == "NickServ":
            self.logs.ircSendMessage(user, ("*" * len(message)))
        else:
            self.logs.ircSendMessage(user, message)
        self.msg(user, message)
        # Flush the logfile

    # Don't use this directy, use sendnotice
    def sendntc(self, user, message):
        #TODO: Better max-length check
        if len(message) > 300:
            message = message[:300] + "..."
        self.logs.ircSendNotice(user, message)
        self.notice(user, message)
        # Flush the logfile

    def send_raw(self, data):
        if self.settings['rate_limit']['raw']['enable']:
            self.rawqueue.append(str(data))
        else:
            self.send_raw_direct(str(data))

    def sendmsg(self, user, message):
        if self.settings['rate_limit']['message']['enable']:
            self.messagequeue.append(str(user) + ":" + str(message))
        else:
            self.sendmessage(user, message)

    def sendnotice(self, user, message):
        if self.settings['rate_limit']['notice']['enable']:
            self.noticequeue.append(str(user) + ":" + str(message))
        else:
            self.sendntc(user, message)

    def senddescribe(self, user, message):
        self.logs.ircSendAction(user, message)
        self.describe(user, message)
        # Flush the logfile

class BotFactory(protocol.ClientFactory):
    protocol = Bot

    def __init__(self):
        # Initialize!
        self.logs = Logger()
        settings = yaml_loader()
        settings = settings.load("config/settings.yml")
        self.nickname = settings["bot"]["nickname"]
        del settings

    def clientConnectionLost(self, connector, reason):
        # We died. Onoes!
        self.logs.warn("Lost connection: %s" % reason)

    def clientConnectionFailed(self, connector, reason):
        # Couldn't connect. Daww!
        self.logs.error("Could not connect: %s" % reason)
