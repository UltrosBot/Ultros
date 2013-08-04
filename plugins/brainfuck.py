# coding=utf-8
from datetime import datetime
from system.yaml_loader import *
from system.decorators import config

class plugin(object):
    """
    Brainfuck; ++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>.
    """

    commands = {
        "brainfuck": "run_brainfuck",
        "bf": "run_brainfuck",
        "brainfucktime": "brainfuck_time"
    }

    def __init__(self, irc):
        self.irc = irc
        self.settings = yaml_loader(True, "brainfuck")

        self.DEFAULT_MAX_EXEC_TIME = 300
        self.max_exec_time = self.DEFAULT_MAX_EXEC_TIME

        self.help = {
            "brainfuck": "Run a snippet of brainfuck code.",
            "brainfucktime": "Set maximum runtime for the brainfuck interpreter."
        }

    def load(self):
        conf = self.settings.load("settings")
        self.set_max_exec_time(conf['max_exec_time'])

    def save(self, data=None):
        self.settings.save_data("settings", {"max_exec_time" : self.max_exec_time})

    def run_brainfuck(self, user, channel, arguments):
        if len(arguments) != 2:
            self.irc.sendnotice(user, "You must give must me some code to eval")
            return
        start_time = datetime.now()
        ended_early = False
        code = arguments[1]
        #Thanks to topo for the interpreter (and original plugin request)
        i, j  = 0, 0
        l = -1
        loops = [0] * 16
        buf = [0] * 30000
        out = ''
        buf_max = 0
        while j < len(code):
            if (datetime.now() - start_time).microseconds / 1000 >= self.max_exec_time:
                ended_early = True
                break
            if code[j] == '+':
                buf[i] += 1
            elif code[j] == '-':
                buf[i] -= 1
            elif code[j] == '>':
                i += 1
                buf_max = max(buf_max, i)
            elif code[j] == '<':
                i = abs(i - 1)
            elif code[j] == '[':
                l += 1
                loops[l] = j
            elif code[j] == ']':
                if buf[i] == 0:
                    j += 1
                    loops[l] = 0
                    l -= 1
                    continue
                else:
                    j = loops[l]
            elif code[j] == '.':
                out += chr(buf[i])
            j += 1

        if ended_early:
            self.irc.sendmsg(channel, "Brainfuck evaluated (ended early) - Result: %s (%s)" % (out, buf[:buf_max]))
        else:
            self.irc.sendmsg(channel, "Brainfuck evaluated - Result: %s (%s)" % (out, buf[:buf_max]))

    @config("rank", "authorized")
    def brainfuck_time(self, user, channel, arguments):
        if len(arguments) == 1:
            self.irc.sendnotice(user, "Brainfuck maximum execution time is %sms" % (self.max_exec_time))
        elif len(arguments) == 2:
            if self.set_max_exec_time(arguments[1]):
                self.irc.sendnotice(user, "Brainfuck maximum execution time has been set to %sms" % (self.max_exec_time))
            else:
                self.irc.sendnotice(user, "Brainfuck maximum execution time has been set to the default %sms" % (self.max_exec_time))

    def set_max_exec_time(self, time):
        success = True
        try:
            time = int(time)
        except ValueError:
            time = -1
        if time <= 0:
            time = self.DEFAULT_MAX_EXEC_TIME
            success = False
        self.max_exec_time = time
        return success

    name = "Brainfuck"
