__author__ = 'Gareth Coles'

import re
import socket
import urlparse
import urllib
import urllib2

from bs4 import BeautifulSoup
from kitchen.text.converters import to_unicode
from netaddr import all_matching_cidrs

from system.plugin import PluginObject

from system.command_manager import CommandManager
from system.event_manager import EventManager

from system.events.general import MessageReceived

from system.protocols.generic.channel import Channel
from system.protocols.generic.user import User

from utils.config import YamlConfig
from utils.data import YamlData, SqliteData


class Plugin(PluginObject):

    channels = None
    commands = None
    events = None
    config = None
    shortened = None

    handlers = {}
    shorteners = {}
    spoofing = {}

    content_types = ["text/html", "text/webviewhtml", "message/rfc822",
                     "text/x-server-parsed-html", "application/xhtml+xml"]

    def setup(self):
        self.logger.debug("Entered setup method.")
        try:
            self.config = YamlConfig("plugins/urls.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
        else:
            if not self.config.exists:
                self.logger.warn("Unable to find config/plugins/urls.yml")
            else:
                self.content_types = self.config["content_types"]
                self.spoofing = self.config["spoofing"]

        self.logger.debug("Spoofing: %s" % self.spoofing)

        self.channels = YamlData("plugins/urls/channels.yml")
        self.shortened = SqliteData("plugins/urls/shortened.sqlite")
        self.commands = CommandManager()
        self.events = EventManager()

        with self.shortened as c:
            c.execute("CREATE TABLE IF NOT EXISTS urls (url TEXT, \
                      shortener TEXT, result TEXT)")

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
        # This second check is a hack to check default group, since there is
        # not currently inheritance
        if not allowed:
            allowed = self.commands.perm_handler.check("urls.title", None,
                                                       target, protocol)

        if not allowed:
            return

        # Strip formatting characters if possible
        message_stripped = message
        try:
            message_stripped = event.caller.utils.strip_formatting(message)
        except AttributeError as e:
            pass

        for word in message_stripped.split(" "):
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

                self.logger.debug("Title: %s" % title)

                if isinstance(target, Channel):
                    if not protocol.name in self.channels:
                        with self.channels:
                            self.channels[protocol.name] = {
                                target.name: {"last": url,
                                              "status": "on",
                                              "shortener":
                                              "tinyurl"}
                            }
                    if not target.name in self.channels[protocol.name]:
                        with self.channels:
                            self.channels[protocol.name][target.name] = {
                                "last": url,
                                "status": "on",
                                "shortener":
                                "tinyurl"
                            }
                    else:
                        with self.channels:
                            self.channels[protocol.name][target.name]["last"] \
                                = url
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
                else:
                    self.logger.warn("Unknown target type: %s [%s]"
                                     % (target, target.__class__))

    def urls_command(self, protocol, caller, source, command, raw_args,
                     parsed_args):
        args = raw_args.split()  # Quick fix for new command handler signature
        if not isinstance(source, Channel):
            caller.respond("This command can only be used in a channel.")
            return
        if len(args) < 2:
            caller.respond("Usage: {CHARS}urls <setting> <value>")
            caller.respond("Operations: set <on/off> - Enable or disable title"
                           " parsing for the current channel")
            caller.respond("            shortener <name> - Set which URL "
                           "shortener to use for the current channel")
            caller.respond("            Shorteners: %s"
                           % ", ".join(self.shorteners.keys()))
            return

        operation = args[0].lower()
        value = args[1].lower()

        if not protocol.name in self.channels:
            with self.channels:
                self.channels[protocol.name] = {
                    source.name: {
                        "status": "on",
                        "last": "",
                        "shortener": "tinyurl"
                    }
                }
        if not source.name in self.channels[protocol.name]:
            with self.channels:
                self.channels[protocol.name][source.name] = {
                    "status": "on",
                    "last": "",
                    "shortener": "tinyurl"
                }

        if operation == "set":
            if not value in ["on", "off"]:
                caller.respond("Usage: {CHARS}urls set <on|off>")
            else:
                with self.channels:
                    self.channels[protocol.name][source.name]["status"] = value
                caller.respond("Title passing for %s turned %s."
                               % (source.name, value))
        elif operation == "shortener":
            if value.lower() in self.shorteners:
                with self.channels:
                    self.channels[protocol.name][source.name]["shortener"] \
                        = value.lower()
                caller.respond("URL shortener for %s set to %s."
                               % (source.name, value))
            else:
                caller.respond("Unknown shortener: %s" % value)
        else:
            caller.respond("Unknown operation: '%s'." % operation)

    def shorten_command(self, protocol, caller, source, command, raw_args,
                        parsed_args):
        args = parsed_args  # Quick fix for new command handler signature
        if not isinstance(source, Channel):
            if len(args) == 0:
                caller.respond("Usage: {CHARS}shorten [url]")
                return
            else:
                handler = "tinyurl"
                url = args[1]
                try:
                    shortened = self.shorten_url(url, handler)
                except Exception as e:
                    self.logger.exception("Error fetching short URL.")
                    caller.respond("Error: %s" % e)
                    return

                caller.respond(shortened)
        else:
            if not protocol.name in self.channels \
               or not source.name in self.channels[protocol.name] \
               or not len(self.channels[protocol.name][source.name]["last"]):
                caller.respond("Nobody's pasted a URL here yet!")
                return
            handler = self.channels[protocol.name][source.name]["shortener"]
            if len(handler) == 0:
                with self.channels:
                    self.channels[protocol.name][source.name]["shortener"]\
                        = "tinyurl"
                handler = "tinyurl"
            if handler not in self.shorteners:
                caller.respond("Shortener '%s' not found - please set a new "
                               "one!" % handler)
                return

            url = self.channels[protocol.name][source.name]["last"]

            if len(args) > 0:
                url = args[0]

            try:
                shortened = self.shorten_url(url, handler)
            except Exception as e:
                self.logger.exception("Error fetching short URL.")
                caller.respond("Error: %s" % e)
                return

            if shortened is None:
                source.respond("Unable to shorten URL %s using handler %s for "
                               "some reason. Poke the bot owner!"
                               % (url, handler))

            source.respond("%s: %s" % (caller.nickname, shortened))

    def tinyurl(self, url):
        return urllib2.urlopen("http://tinyurl.com/api-create.php?url="
                               + urllib.quote_plus(url)).read()

    def parse_title(self, url, use_handler=True):
        domain = ""
        self.logger.debug("Url: %s" % url)
        try:
            parsed = urlparse.urlparse(url)
            domain = parsed.hostname

            ip = socket.gethostbyname(domain)

            matches = all_matching_cidrs(ip, ["10.0.0.0/8", "0.0.0.0/8",
                                              "172.16.0.0/12",
                                              "192.168.0.0/16", "127.0.0.0/8"])

            if matches:
                self.logger.warn("Prevented a portscan: %s" % url)
                return None, None

            if domain.startswith("www."):
                domain = domain[4:]

            if domain in self.handlers and use_handler:
                try:
                    result = self.handlers[domain](url)
                    if result:
                        return to_unicode(result), None
                except Exception:
                    self.logger.exception("Error running handler, parsing "
                                          "title normally.")

            self.logger.debug("Parsed domain: %s" % domain)

            request = urllib2.Request(url)
            if domain in self.spoofing:
                self.logger.debug("Custom spoofing for this domain found.")
                user_agent = self.spoofing[domain]
                if user_agent:
                    self.logger.debug("Spoofing user-agent: %s" % user_agent)
                    request.add_header("User-agent", user_agent)
                else:
                    self.logger.debug("Not spoofing user-agent.")
            else:
                self.logger.debug("Spoofing Firefox as usual.")
                request.add_header('User-agent', 'Mozilla/5.0 (X11; U; Linux '
                                                 'i686; en-US; rv:1.9.0.1) '
                                                 'Gecko/2008071615 Fedora/3.0.'
                                                 '1-1.fc9-1.fc9 Firefox/3.0.1')
            response = urllib2.urlopen(request)

            self.logger.debug("Info: %s" % response.info())

            headers = response.info().headers
            new_url = response.geturl()
            if "//" in new_url:
                new_url = new_url.split("//")[1]
            domain = new_url.split("/")[0]

            headers_dict = {}

            for x in headers:
                k, v = x.split(": ", 1)

                headers_dict[k.lower()] = v.strip("\r\n")

            status_code = response.getcode()

            if status_code in [301, 302, 303, 307, 308]:
                return self.parse_title(headers["location"])

            ct = headers_dict["content-type"]
            if ";" in ct:
                ct = ct.split(";")[0]

            self.logger.debug("Content-type: %s" % repr(ct))

            if ct not in self.content_types:
                self.logger.debug("Content-type is not allowed.")
                return None, None

            page = response.read()
            soup = BeautifulSoup(page)
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
                title = re.sub("\s+", " ", title)
                title = to_unicode(title)
                domain = to_unicode(domain)
                return title, domain
            else:
                return None, None
        except Exception as e:
            if not str(e).lower() == "not viewing html":
                self.logger.exception("Error parsing title.")
                return str(e), domain
            return None, None

    def shorten_url(self, url, handler):
        with self.shortened as c:
            self.logger.debug("URL: %s" % url)
            self.logger.debug("Handler: %s" % handler)
            c.execute("SELECT * FROM urls WHERE  url=? AND shortener=?",
                      (url, handler.lower()))
            r = c.fetchone()
            self.logger.debug("Result (SQL): %s" % repr(r))
            if not r is None:
                return r[2]
        if handler in self.shorteners:
            result = self.shorteners[handler](url)
            with self.shortened as c:
                c.execute("INSERT INTO urls VALUES (?, ?, ?)",
                          (url, handler.lower(), result))
            return result
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
