__author__ = 'Gareth Coles'

import urlparse
import urllib
import urllib2

from utils.data import Data

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.plugin import PluginObject

from system.events.general import MessageReceived

from system.protocols.generic.channel import Channel
from system.protocols.generic.user import User

try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup


class Plugin(PluginObject):

    channels = None
    commands = None
    events = None

    handlers = {}
    shorteners = {}

    content_types = ["text/html", "text/webviewhtml", "message/rfc822",
                     "text/x-server-parsed-html", "application/xhtml+xml"]

    def setup(self):
        self.logger.debug("Entered setup method.")
        self.channels = Data("plugins/urls/channels.yml")
        self.commands = CommandManager.instance()
        self.events = EventManager.instance()

        def message_event_filter(event=MessageReceived):
            target = event.target
            type_ = event.type

            return type_ == "message" \
                or isinstance(target, Channel) \
                or isinstance(target, User)

        self.add_shortener("tinyurl", self.tinyurl)

        self.events.add_callback("MessageReceived", self, self.message_handler,
                                 1, message_event_filter)
        self.commands.register_command("urls", self.urls_command, self,
                                       "urls.manage")
        self.commands.register_command("shorten", self.shorten_command, self,
                                       "urls.shorten")

    def message_handler(self, event=MessageReceived):
        protocol = event.caller
        source = event.source
        target = event.target
        message = event.message

        allowed = self.commands.perm_handler.check("urls.title", source,
                                                   target, protocol)
        if not allowed:
            allowed = self.commands.perm_handler.check("urls.title", None,
                                                       target, protocol)

        if not allowed:
            if isinstance(target, User):
                source.respond("You're not authorized to use the URL title "
                               "fetcher.")
                return

        for word in message.split(" "):
            pos = word.lower().find("http://")
            if pos == -1:
                pos = word.lower().find("https://")
            if pos > -1:
                end = word.lower().find(" ", pos)
                if end > -1:
                    url = word[pos:end]
                else:
                    url = word[pos:]

                title, domain = self.parse_title(url)

                if isinstance(target, Channel):
                    if not target.name in self.channels:
                        with self.channels:
                            self.channels[target.name] = {"last": url,
                                                          "status": "on",
                                                          "shortener":
                                                          "tinyurl"}
                    else:
                        with self.channels:
                            self.channels[target.name]["last"] = url
                    if title is None:
                        return

                    if domain is not None and "/" in domain:
                        domain = domain.split("/")[0]
                    if domain is None:
                        target.respond(title)
                    else:
                        target.respond("\"%s\" at %s" % (title, domain))
                elif isinstance(target, User):
                    if title is None:
                        return

                    if domain is not None and "/" in domain:
                        domain = domain.split("/")[0]
                    if domain is None:
                        source.respond(title)
                    else:
                        source.respond("\"%s\" at %s" % (title, domain))

    def urls_command(self, caller, source, args, protocol):
        if not isinstance(source, Channel):
            caller.respond("This command can only be used in a channel.")
            return
        if len(args) < 2:
            caller.respond("Usage: {CHARS}urls <setting> <value>")
            caller.respond("Operations: set <on/off> - Enable or disable title"
                           " parsing for the current channel")
            caller.respond("            shortener <name> - Set which URL "
                           "shortener to use for the current channel")
            return

        operation = args[0].lower()
        value = args[1].lower()
        if operation == "set":
            if value in ["on", "off"]:
                caller.respond("Usage: {CHARS}urls set <on|off>")
            else:
                if not source.name in self.channels:
                    with self.channels:
                        self.channels[source.name] = {"status": "on",
                                                      "last": "",
                                                      "shortener": "tinyurl"}
                with self.channels:
                    self.channels[source.name]["status"] = value
                caller.respond("Title passing for %s turned %s."
                               % (source.name, value))
        elif operation == "shortener":
            if value.lower() in self.shorteners:
                if not source.name in self.channels:
                    with self.channels:
                        self.channels[source.name] = {"status": "on",
                                                      "last": "",
                                                      "shortener": "tinyurl"}
                with self.channels:
                    self.channels[source.name]["shortener"] = value.lower()
                caller.respond("URL shortener for %s set to %s."
                               % (source.name, value))
            else:
                caller.respond("Unknown shortener: %s" % value)
        else:
            caller.respond("Unknown operation: '%s'." % operation)

    def shorten_command(self, caller, source, args, protocol):
        if not isinstance(source, Channel):
            if len(args) == 0:
                caller.respond("Usage: {CHARS}shorten [url]")
                return
            else:
                handler = "tinyurl"
                url = args[1]
                shortened = self.shorten_url(url, handler)

                caller.respond(shortened)
        else:
            if not source.name in self.channels \
               or not len(self.channels[source.name]["last"])\
               and not len(self.channels[source.name]["last"]):
                caller.respond("Nobody's pasted a URL here yet!")
                return
            handler = self.channels[source.name]["shortener"]
            if len(handler) == 0:
                with self.channels:
                    self.channels[source.name]["shortener"] = "tinyurl"
                handler = "tinyurl"
            if handler not in self.shorteners:
                caller.respond("Shortener '%s' not found - please set a new "
                               "one!" % handler)
                return

            url = self.channels[source.name]["last"]

            if len(args) > 0:
                url = args[1]

            shortened = self.shorten_url(url, handler)

            source.respond("%s: %s" % (caller.nickname, shortened))

    def tinyurl(self, url):
        return urllib2.urlopen("http://tinyurl.com/api-create.php?url="
                               + urllib.quote_plus(url)).read()

    def parse_title(self, url):
        domain = ""
        self.logger.debug("Url: %s" % url)
        try:
            parsed = urlparse.urlparse(url)
            domain = parsed.hostname

            if domain.startswith("www."):
                domain = domain[4:]

            if domain in self.handlers:
                return self.handlers[domain](url), None

            self.logger.debug("Parsed domain: %s" % domain)

            request = urllib2.Request(url)
            request.add_header('User-agent', 'Mozilla/5.0 (X11; U; Linux i686;'
                                             ' en-US; rv:1.9.0.1) Gecko/200807'
                                             '1615 Fedora/3.0.1-1.fc9-1.fc9 Fi'
                                             'refox/3.0.1')
            response = urllib2.urlopen(request)

            self.logger.debug("Info: %s" % response.info())

            headers = response.info().headers
            new_url = response.geturl()
            if "//" in new_url:
                new_url = new_url.split("//")[1]
            domain = new_url.split("/")[0]

            headers_dict = {}

            for x in headers:
                k, v = x.split(": ")

                headers_dict[k.lower()] = v.strip("\r\n")

            status_code = response.getcode()

            if status_code in [301, 302, 303, 307, 308]:
                return self.parse_title(headers["location"])

            ct = headers_dict["content-type"]
            if ";" in ct:
                ct = ct.split(";")[0]

            self.logger.debug("Content-type: %s" % repr(ct))

            if ct not in self.content_types:
                return None, None

            page = response.read()
            soup = BeautifulSoup(page,
                                 convertEntities=BeautifulSoup.HTML_ENTITIES)
            title = unicode(soup.title.string).encode("UTF-8")
            return title, domain
        except Exception as e:
            if not str(e).lower() == "not viewing html":
                return str(e), domain
            return None, None

    def shorten_url(self, url, handler):
        if handler in self.shorteners:
            return self.shorteners[handler](url)
        return None

    def add_handler(self, domain, handler):
        if domain.startswith("www."):
            raise ValueError("Domain should not start with 'www.'")
        if domain not in self.handlers:
            self.logger.debug("Handler registered for '%s': %s"
                              % (domain, handler))
            self.handlers[domain] = handler
            return True
        return False

    def add_shortener(self, name, handler):
        if name not in self.shorteners:
            self.logger.debug("Shortener '%s' registered: %s"
                              % (name, handler))
            self.shorteners[name] = handler
            return True
        return False
