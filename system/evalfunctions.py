# coding=utf-8
from math import *
import urllib, urllib2, re, hashlib, random, time, json

class evalFunctions(object):
    def __init__(self, bot):
        self.bot = bot

    def seval(self, command, cinfo):
        user = cinfo["user"]
        host = cinfo["hostmask"]
        origin = cinfo["origin"]
        message = cinfo["message"]
        target = cinfo["target"]

        COLOUR = self.bot.col
        COLOR = COLOUR
        BOLD = self.bot.bold
        ITALIC = self.bot.ital
        UNDERLINE = self.bot.under
        REVERSE = self.bot.reverse
        CTCP = self.bot.ctcp

        md5 = self.md5
        wget = self.wget
        randint = self.randint
        msg = self.msg
        notice = self.notice
        join = self.join
        part = self.part
        kick = self.kick
        mode = self.mode
        toJson = self.toJson
        fromJson = self.fromJson

        del self
        try:
            value = str(unicode(eval(command)).encode("LATIN-1", "replace"))
        except Exception as e:
            value = str(e)
        except SystemExit:
            value = "ERROR: Tried to call a SystemExit!"
        return value

    def randint(self, lo, hi):
        random.seed()
        return random.randint(lo, hi)

    def toJson(self, obj):
        return json.dumps(obj)

    def fromJson(self, obj):
        return json.loads(obj)

    def md5(self, data):
        return hashlib.md5(data).hexdigest()

    def wget(self, url):
        try:
            page = urllib2.urlopen(url)
        except Exception as e:
            return str(e)
        test = self.wtest(page)
        if not test[0]:
            return test[1]
        else:
            data = page.read()
            if len(data) > (1024 * 5):
                return "Content is greater than 5KB in size."
            # elif data.count("\n") > 3:
            #     return "Content contains more than three newlines."
            else:
                return self.rht(data)

    def wtest(self, message):
        info = message.info()
        typec = info["Content-Type"].lower()
        if ";" in typec:
            typec = typec.split(";")[0]
        try:
            length = int(info["Content-Length"])
        except:
            length = 0
        if message.geturl().startswith("file:/"):
            return [False, "Local file access is not allowed."]
        if not (typec == "text/html" or typec == "text/plain" or typec == "text/json"):
            return [False, "Content-Type " + typec + " is not allowed."]
        elif length > (1024 * 5):
            return [False, "Content is greater than 5KB in size."]
        return [True, ""]

    def msg(self, target, message, flag=False):
        try:
            self.bot.sendmsg(target, message)
        except:
            if flag:
                return "Couldn't send message!"
            else:
                return ""
        else:
            if flag:
                return "Message sent!"
            else:
                return ""

    def notice(self, target, message, flag=False):
        try:
            self.bot.sendnotice(target, message)
        except:
            if flag:
                return "Couldn't send notice!"
            else:
                return ""
        else:
            if flag:
                return "Message sent!"
            else:
                return ""

    def join(self, channel, flag=False):
        try:
            self.bot.join(channel)
        except:
            if flag:
                return "Couldn't join channel!"
            else:
                return ""
        else:
            if flag:
                return "Channel joined!"
            else:
                return ""

    def part(self, channel, message="Leaving", flag=False):
        try:
            self.bot.sendLine("PART %s :%s" % (channel, message))
        except:
            if flag:
                return "Couldn't part channel!"
            else:
                return ""
        else:
            if flag:
                return "Channel parted!"
            else:
                return ""

    def kick(self, channel, target, message="", flag=False):
        if message == "":
            message = target
        try:
            if self.bot.is_op(channel, self.bot.nickname):
                self.bot.sendLine("KICK %s %s :%s" % (channel, target, message))
            else:
                return "Don't have op in that channel!"
        except:
            if flag:
                return "Couldn't kick user!"
            else:
                return ""
        else:
            if flag:
                return "Kicked user!"
            else:
                return ""

    def mode(self, channel, modes, targets="", flag=False):
        try:
            if self.bot.is_op(channel, self.bot.nickname):
                self.bot.sendLine("MODE %s %s %s" % (channel, modes, targets))
            else:
                return "Don't have op in that channel!"
        except:
            if flag:
                return "Couldn't send mode!"
            else:
                return ""
        else:
            if flag:
                return "Mode set!"
            else:
                return ""

    def rht(self, data):
    # Utility, removes HTML from the input
        p = re.compile(r'<.*?>')
        try:
            return p.sub('', data.encode('LATIN-1', 'replace'))
        except:
            return "Unable to parse HTML."
