__author__ = 'Gareth'

import sys
import time


from twisted.internet import reactor
from threading import Thread

from utils.console import getch, getTerminalSize
from utils.log import getLogger


WIDTH = 0

if sys.stdout.isatty():
    WIDTH = getTerminalSize()[0] - 1


class ConsoleMagic(object):
    wrapper = None
    reader = None
    old_stdout = None
    logger = None

    wrapped = True

    def __init__(self):
        if not sys.stdout.isatty() or "--no-console" in sys.argv:
            self.wrapped = False
            return

        self.logger = getLogger("Console")

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr

        self.wrapper = Wrapper(self)
        self.wrapper_err = WrapperErr(self)
        self.reader = Reader(self)

        # We set it here
        sys.stdout = self.wrapper
        sys.stderr = self.wrapper_err

    def unwrap(self):
        if self.wrapped:
            self.reader.do_stop()
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr
            sys.stdout.write(u"\r%s\r" % (" " * WIDTH))
            self.wrapped = False

    def written(self, p_str):
        self.old_stdout.write(u"\r")
        self.old_stdout.flush()

        newlined = False

        for x in p_str:
            if newlined:
                newlined = False
                self.old_stdout.write(u"\r%s\r" % (" " * WIDTH))

            self.old_stdout.write(x)
            if x == "\n":
                self.old_stdout.write(u"> %s" % self.reader.buffer)
                self.old_stdout.flush()
                newlined = True

        self.old_stdout.flush()

    def written_err(self, p_str):
        self.old_stdout.write(u"\r")
        self.old_stdout.flush()

        newlined = False

        for x in p_str:
            if newlined:
                newlined = False
                self.old_stdout.write(u"\r%s\r" % (" " * WIDTH))

            self.old_stderr.write(x)
            self.old_stderr.flush()
            if x == "\n":
                self.old_stdout.write(u"> %s" % self.reader.buffer)
                self.old_stdout.flush()
                newlined = True

        self.old_stdout.flush()

    def read(self, buffer):
        self.old_stdout.write(u"\r\n")
        self.logger.info(u"Input: %s" % buffer)
        self.old_stdout.write(u"> ")


class Wrapper(object):
    magic = None

    def __init__(self, magic):
        """
        :type magic: ConsoleMagic
        """

        self.magic = magic

    def write(self, p_str):
        self.magic.written(p_str)

    def __getattribute__(self, name):
        try:
            # Check our attributes
            return object.__getattribute__(self, name)
        except AttributeError:
            # If not, get them on the old stdout
            return self.magic.old_stdout.__getattribute__(name)


class WrapperErr(object):
    magic = None

    def __init__(self, magic):
        """
        :type magic: ConsoleMagic
        """

        self.magic = magic

    def write(self, p_str):
        self.magic.written_err(p_str)

    def __getattribute__(self, name):
        try:
            # Check our attributes
            return object.__getattribute__(self, name)
        except AttributeError:
            # If not, get them on the old stderr
            return self.magic.old_stderr.__getattribute__(name)


class Reader(Thread):
    magic = None
    buffer = u""

    stop = False

    def __init__(self, magic):
        """
        :type magic: ConsoleMagic
        """

        super(Reader, self).__init__()

        self.magic = magic
        self.setDaemon(True)
        self.start()

    def run(self):
        while not self.stop:
            char = getch()

            if char == u"\r" or char == u"\n":
                reactor.callFromThread(self.magic.read, self.buffer)
                self.buffer = u""
            elif char == u"\x03":
                self.stop = True
                reactor.callFromThread(self.ctrl_c)
            elif char == u"\b":
                if self.buffer:
                    self.magic.old_stdout.write(u"\b")
                    self.magic.old_stdout.write(u" ")
                    self.magic.old_stdout.write(u"\b")
                    self.buffer = self.buffer[:-1]
            elif char == u"\xe0" or char == u"\x00":
                getch()
            else:
                self.magic.old_stdout.write(char)
                self.buffer += char

            time.sleep(0.001)

    def ctrl_c(self):
        self.magic.unwrap()

        from system.factory_manager import Manager
        Manager().unload()

    def do_stop(self):
        self.stop = True
