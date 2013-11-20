__author__ = 'Gareth Coles'

import urlparse
import urllib2
try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup

from utils.data import Data

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.plugin import PluginObject

from system.events.general import MessageReceived

from system.protocols.generic.channel import Channel
from system.protocols.generic.user import User


class Plugin(PluginObject):

    channels = None
    commands = None
    events = None

    handlers = {}

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

        self.events.add_callback("MessageReceived", self, self.message_handler,
                                 1, message_event_filter)
        self.commands.register_command("urls", self.urls_command, self,
                                       "urls.manage")

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

        for word in message.lower().split(" "):
            pos = word.find("http://")
            if pos == -1:
                pos = word.find("https://")
            if pos > -1:
                end = word.find(" ", pos)
                if end > -1:
                    url = word[pos:end]
                else:
                    url = word[pos:]

                title, domain = self.parse_title(url)

                if title is None or domain is None:
                    return

                if "/" in domain:
                    domain = domain.split("/")[0]

                if isinstance(target, Channel):
                    if not target.name in self.channels:
                        self.channels[target.name] = {"last": url,
                                                      "status": "on",
                                                      "shortener": ""}
                    else:
                        self.channels[target.name]["last"] = url
                    target.respond("\"%s\" at %s" % (title, domain))
                elif isinstance(target, User):
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
                caller.respond("Usage: {CHARs}urls set <on|off>")
            else:
                self.channels[source.name]["status"] = value
                caller.respond("Title passing for %s turned %s."
                               % (source.name, value))
        elif operation == "shortener":
            caller.respond("Shortener setting not implemented yet.")
        else:
            caller.respond("Unknown operation: '%s'." % operation)

    def parse_title(self, url):
        domain = ""
        try:
            parsed = urlparse.urlparse(url)
            domain = parsed.hostname

            if domain.startswith("www."):
                domain = domain[4:]

            if domain in self.handlers:
                return self.handlers[domain](url)

            request = urllib2.Request(url)
            request.add_header('User-agent', 'Mozilla/5.0 (X11; U; Linux i686;'
                                             ' en-US; rv:1.9.0.1) Gecko/200807'
                                             '1615 Fedora/3.0.1-1.fc9-1.fc9 Fi'
                                             'refox/3.0.1')
            response = urllib2.urlopen(request)

            self.logger.debug("Info: %s" % response.info())

            headers = response.info().headers
            headers_dict = {}

            for x in headers:
                k, v = x.split(": ")

                headers_dict[k] = v.strip("\r\n")

            status_code = response.getcode()

            if status_code in [301, 302, 303, 307, 308]:
                return self.parse_title(headers["Location"])

            page = response.read()
            soup = BeautifulSoup(page)
            title = unicode(soup.title.string).encode("UTF-8")
            return title, domain
        except Exception as e:
            if not str(e).lower() == "not viewing html":
                return str(e), domain
            return None, None

    def add_handler(self, domain, handler):
        if domain.startswith("www."):
            raise ValueError("Domain should not start with 'www.'")
        if domain not in self.handlers:
            self.logger.debug("Handler registered for '%s': %s"
                              % (domain, handler))
            self.handlers[domain] = handler
            return True
        return False
