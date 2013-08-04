import os
import time
import sys

from system.constants import *

class Logger(object):

    cols = []

    def __init__(self):
        # Generate a list of all possible colour codes
        for x in range(0, 16):
            for y in range(0, 16):
                self.cols.append(col + str(x).zfill(2) + "," + str(y).zfill(2) )
        self.cols.append(bold)
        self.cols.append(under)
        self.cols.append(ital)
        self.cols.append(reverse)
        self.cols.append(normal)
        self.cols.append(ctcp)

        if not os.path.exists("logs"):
            os.mkdir("logs")
        if not os.path.exists("logs/channels"):
            os.mkdir("logs/channels")
        if not os.path.exists("logs/private"):
            os.mkdir("logs/private")

    # Internal functions

    def _strip(self, message):
        """Strip all colour codes from a message"""
        message = str(message) # TYPE SAFETY
        for col in self.cols:
            message.replace(col, "")
        return message

    def _getTimestamp(self):
        """Get a timestamp in the correct format"""
        return time.strftime("%H:%M:%S")

    def _write(self, file, message):
        """Write a message to a file"""
        file = file.replace("/", "_SLASH_").replace("\\", "_BACKSLASH_").replace("|", "_PIPE_")
        fh = open("logs/" + file, "a")
        fh.write(message + "\n")
        fh.flush()
        fh.close()

    def _print(self, message):
        """Output to stdout"""
        sys.stdout.write(message + "\n")

    def _err(self, message):
        """Output to stderr"""
        sys.stderr.write(message + "\n")

    # Logging levels

    def info(self, message, toFile=True):
        """Log a message with the INFO warning level"""
        message = self._strip(message)
        f_string = "%s | INFO | %s" % (self._getTimestamp(), message)
        if toFile:
            self._write("info.log", f_string)
        self._print(f_string)

    def warn(self, message, toFile=True):
        """Log a message with the WARN warning level"""
        message = self._strip(message)
        f_string = "%s | WARN | %s" % (self._getTimestamp(), message)
        if toFile:
            self._write("warn.log", f_string)
        self._print(f_string)

    def error(self, message, toFile=True):
        """Log a message with the ERROR warning level"""
        message = self._strip(message)
        f_string = "%s | ERROR| %s" % (self._getTimestamp(), message)
        if toFile:
            self._write("error.log", f_string)
        self._err(f_string)

    # Section-specific logging

    def web(self, request):
        """Internal, logs details aboout a web request"""
        f_string = "[WEB] %s %s: %s" % (request.getClientIP(), request.method, request.uri)
        self._write("web.log", f_string)
        self._print(f_string)

    def ircPublic(self, user, channel, message):
        """Internal, log a message from a channel"""
        message = self._strip(message)
        f_string = "%s <%s> %s" % (channel, user, message)
        self.info(f_string, False)
        filename = "channels/%s.log" % channel
        line = "<%s> %s" % (user, message)
        self._write(filename, line)

    def ircPrivate(self, user, message):
        """Internal, log a message from a query"""
        message = self._strip(message)
        f_string = "<%s> %s" % (user, message)
        self.info(f_string, False)
        filename = "private/%s.log" % user
        line = "<%s> %s" % (user, message)
        self._write(filename, line)

    def ircPublicAction(self, user, channel, message):
        """Internal, log an action from a channel"""
        message = self._strip(message)
        f_string = "%s * %s %s" % (channel, user, message)
        self.info(f_string, False)
        filename = "channels/%s.log" % channel
        line = "* %s %s" % (user, message)
        self._write(filename, line)

    def ircPrivateAction(self, user, message):
        """Internal, log an action from a query"""
        message = self._strip(message)
        f_string = "* %s %s" % (user, message)
        self.info(f_string, False)
        filename = "private/%s.log" % user
        line = "* %s %s" % (user, message)
        self._write(filename, line)

    def ircModesSet(self, target, user, modes, args, set):
        """Internal, log some modes that were set"""
        f_string = "%s set mode %s %s%s %s" % (user, target, "+" if set else "-", modes, args)
        self.info(f_string, False)
        if target.startswith("#"):
            filename = "channels/%s.log" % target
        else:
            filename = "private/%s.log" % target
        line = "%s set mode %s%s %s" % (user, "+" if set else "-", modes, args)
        self._write(filename, line)

    def ircSendMessage(self, target, message):
        """Internal, log a message we sent"""
        message = self._strip(message)
        f_string = "%s -> %s" % (target, message)
        self.info(f_string, False)
        if target.startswith("#"):
            filename = "channels/%s.log" % target
        else:
            filename = "private/%s.log" % target
        line = "-> %s" % (message)
        self._write(filename, line)

    def ircSendNotice(self, target, message):
        """Internal, log a notice we sent"""
        message = self._strip(message)
        f_string = "%s -> -%s-" % (target, message)
        self.info(f_string, False)
        if target.startswith("#"):
            filename = "channels/%s.log" % target
        else:
            filename = "private/%s.log" % target
        line = "-> -%s-" % (message)
        self._write(filename, line)

    def ircSendAction(self, target, message):
        """Internal, log an action we sent"""
        message = self._strip(message)
        f_string = "%s -> * %s" % (target, message)
        self.info(f_string, False)
        if target.startswith("#"):
            filename = "channels/%s.log" % target
        else:
            filename = "private/%s.log" % target
        line = "-> * %s" % (message)
        self._write(filename, line)

##     Logging to the admin channel
#    def chanLog(self, irc, message):
#        """Log a message to the admin channel"""
#        pass
##     Out of the scope of this logger

#Logger()
