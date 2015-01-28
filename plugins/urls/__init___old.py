"""
A plugin to provide various URL-related tools and services.

This plugin does quite a lot of things - URL title parsing, URL shortening,
URL logging to database, specialized URL handlers.. Its partner plugin,
URL-tools (in the contrib repo) extends its functionality using the API it
exposes.
"""

__author__ = 'Gareth Coles'

import fnmatch
import re
import socket
import urlparse
import urllib
import urllib2

from bs4 import BeautifulSoup
from kitchen.text.converters import to_unicode
from netaddr import all_matching_cidrs

from system.command_manager import CommandManager
from system.decorators.threads import run_async_threadpool
from system.event_manager import EventManager
from system.events.general import MessageReceived

import system.plugin as plugin

from system.protocols.generic.channel import Channel
from system.protocols.generic.user import User

from system.storage.formats import YAML, DBAPI
from system.storage.manager import StorageManager

from system.translations import Translations
_ = Translations().get()
__ = Translations().get_m()


class URLsPlugin(plugin.PluginObject):
    """
    URLs plugin object
    """

    channels = None
    commands = None
    config = None
    events = None
    shortened = None
    storage = None

    blacklist = []
    handlers = {}
    shorteners = {}
    spoofing = {}

    content_types = ["text/html", "text/webviewhtml", "message/rfc822",
                     "text/x-server-parsed-html", "application/xhtml+xml"]

    def setup(self):
        """
        Called when the plugin is loaded. Performs initial setup.
        """

        self.logger.trace(_("Entered setup method."))
        self.storage = StorageManager()
        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/urls.yml")
        except Exception:
            self.logger.exception(_("Error loading configuration!"))
        else:
            if not self.config.exists:
                self.logger.warn(_("Unable to find config/plugins/urls.yml"))
            else:
                self.content_types = self.config["content_types"]
                self.spoofing = self.config["spoofing"]

        self.logger.debug(_("Spoofing: %s") % self.spoofing)

        self.channels = self.storage.get_file(self, "data", YAML,
                                              "plugins/urls/channels.yml")
        self.shortened = self.storage.get_file(
            self,
            "data",
            DBAPI,
            "sqlite3:data/plugins/urls/shortened.sqlite",
            "data/plugins/urls/shortened.sqlite",
            check_same_thread=False
        )

        self.commands = CommandManager()
        self.events = EventManager()

        self.reload()

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
                                       "urls.shorten", default=True)

    def reload(self):
        """
        Reload files and create tables as necessary
        """

        self.shortened.runQuery("CREATE TABLE IF NOT EXISTS urls ("
                                "url TEXT, "
                                "shortener TEXT, "
                                "result TEXT)")

        self.blacklist = []
        blacklist = self.config.get("blacklist", [])

        for element in blacklist:
            try:
                self.blacklist.append(re.compile(element))
            except Exception:
                self.logger.exception("Unable to compile regex '%s'" % element)

    def check_blacklist(self, url):
        """
        Check whether a URL is in the user-defined blacklist

        :param url: The URL to check
        :type url: str

        :return: Whether the URL is in the blacklist
        :rtype: bool
        """

        for pattern in self.blacklist:
            try:
                self.logger.debug(_("Checking pattern '%s' against URL '%s'")
                                  % (pattern, url))
                if re.match(pattern, url):
                    return True
            except Exception as e:
                self.logger.debug(_("Error in pattern matching: %s") % e)
                return False
        return False

    @run_async_threadpool
    def message_handler(self, event=MessageReceived):
        """
        Event handler for general messages
        """

        protocol = event.caller
        source = event.source
        target = event.target
        message = event.message

        allowed = self.commands.perm_handler.check("urls.title", source,
                                                   target, protocol)

        if not allowed:
            return

        # PEP = wat sometimes
        if self.channels.get(protocol.name,
                             {}).get(target.name,
                                     {}).get("status", "on") == "off":
            return

        # Strip formatting characters if possible
        message_stripped = message
        try:
            message_stripped = event.caller.utils.strip_formatting(message)
        except AttributeError:
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

                if url in ["http://", "https://"]:
                    self.logger.trace(_("URL is not actually a URL, just %s"
                                        % url))
                    return

                if self.check_blacklist(url):
                    self.logger.debug(_("Not parsing, URL is blacklisted."))
                    return

                title, domain = self.parse_title(url)

                self.logger.trace(_("Title: %s") % title)

                if isinstance(target, Channel):
                    if protocol.name not in self.channels:
                        with self.channels:
                            self.channels[protocol.name] = {
                                target.name: {"last": url,
                                              "status": "on",
                                              "shortener":
                                              "tinyurl"}
                            }
                    if target.name not in self.channels[protocol.name]:
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
                    self.logger.warn(_("Unknown target type: %s [%s]")
                                     % (target, target.__class__))

    def urls_command(self, protocol, caller, source, command, raw_args,
                     parsed_args):
        """
        Command handler for the urls command
        """

        args = raw_args.split()  # Quick fix for new command handler signature
        if not isinstance(source, Channel):
            caller.respond(__("This command can only be used in a channel."))
            return
        if len(args) < 2:
            caller.respond(__("Usage: {CHARS}urls <setting> <value>"))
            caller.respond(__("Operations: set <on/off> - Enable or disable "
                              "title parsing for the current channel"))
            caller.respond("            %s" % __("shortener <name> - Set "
                                                 "which URL shortener to use "
                                                 "for the current channel"))
            caller.respond("            %s" % __("Shorteners: %s")
                           % ", ".join(self.shorteners.keys()))
            return

        operation = args[0].lower()
        value = args[1].lower()

        if protocol.name not in self.channels:
            with self.channels:
                self.channels[protocol.name] = {
                    source.name: {
                        "status": "on",
                        "last": "",
                        "shortener": "tinyurl"
                    }
                }
        if source.name not in self.channels[protocol.name]:
            with self.channels:
                self.channels[protocol.name][source.name] = {
                    "status": "on",
                    "last": "",
                    "shortener": "tinyurl"
                }

        if operation == "set":
            if value not in [__("on"), __("off")]:
                caller.respond(__("Usage: {CHARS}urls set <on|off>"))
            else:
                with self.channels:
                    if value == __("on"):
                        value = "on"
                    elif value == __("off"):
                        value = "off"
                    self.channels[protocol.name][source.name]["status"] = value
                caller.respond(__("Title passing for %s turned %s.")
                               % (source.name, __(value)))
        elif operation == "shortener":
            if value.lower() in self.shorteners:
                with self.channels:
                    self.channels[protocol.name][source.name]["shortener"] \
                        = value.lower()
                caller.respond(__("URL shortener for %s set to %s.")
                               % (source.name, value))
            else:
                caller.respond(__("Unknown shortener: %s") % value)
        else:
            caller.respond(__("Unknown operation: '%s'.") % operation)

    def _respond_shorten(self, result, source, handler):
        """
        Respond to a shorten command, after a successful Deferred
        """

        if result is not None:
            return source.respond(result)
        return source.respond(__("Unable to shorten using handler %s. Poke the"
                                 "bot owner!")
                              % handler)

    def _respond_shorten_fail(self, failure, source, handler):
        """
        Respond to a shorten command, after a failed Deferred
        """

        return source.respond(__("Error shortening url with handler %s: %s")
                              % (handler, failure))

    def shorten_command(self, protocol, caller, source, command, raw_args,
                        parsed_args):
        """
        Command handler for the shorten command
        """

        args = parsed_args  # Quick fix for new command handler signature
        if not isinstance(source, Channel):
            if len(args) == 0:
                caller.respond(__("Usage: {CHARS}shorten [url]"))
                return
            else:
                handler = "tinyurl"
                url = args[0]
                try:
                    d = self.shorten_url(url, handler)
                    d.addCallbacks(self._respond_shorten,
                                   self._respond_shorten_fail,
                                   callbackArgs=(source, handler),
                                   errbackArgs=(source, handler))
                except Exception as e:
                    self.logger.exception(_("Error fetching short URL."))
                    caller.respond(__("Error: %s") % e)
                    return
        else:
            if protocol.name not in self.channels \
               or source.name not in self.channels[protocol.name] \
               or not len(self.channels[protocol.name][source.name]["last"]):
                caller.respond(__("Nobody's pasted a URL here yet!"))
                return
            handler = self.channels[protocol.name][source.name]["shortener"]
            if len(handler) == 0:
                with self.channels:
                    self.channels[protocol.name][source.name]["shortener"]\
                        = "tinyurl"
                handler = "tinyurl"
            if handler not in self.shorteners:
                caller.respond(__("Shortener '%s' not found - please set a "
                                  "new one!") % handler)
                return

            url = self.channels[protocol.name][source.name]["last"]

            if len(args) > 0:
                url = args[0]

            try:
                d = self.shorten_url(url, handler)
                d.addCallbacks(self._respond_shorten,
                               self._respond_shorten_fail,
                               callbackArgs=(source, handler),
                               errbackArgs=(source, handler))
            except Exception as e:
                self.logger.exception(_("Error fetching short URL."))
                caller.respond(__("Error: %s") % e)
                return

    def tinyurl(self, url):
        """
        Shorten a URL with TinyURL. Don't use this directly.
        """

        return urllib2.urlopen("http://tinyurl.com/api-create.php?url="
                               + urllib.quote_plus(url)).read()

    def parse_title(self, url, use_handler=True):
        """
        Get and return the page title for a URL, or the title from a
        specialized handler, if one is registered.

        This function returns a tuple which may be one of these forms..

        * (title, None) if the title was fetched by a specialized handler
        * (title, domain) if the title was parsed from the HTML
        * (None, None) if fetching the title was entirely unsuccessful.
            This occurs in each of the following cases..

            * When a portscan is detected and stopped
            * When the page simply has no title
            * When there is an exception in the chain somewhere

        :param url: The URL to check
        :param use_handler: Whether to use specialized handlers

        :type url: str
        :type use_handler: bool

        :returns: A tuple containing the result
        :rtype: tuple(None, None), tuple(str, str), tuple(str, None)
        """

        domain = ""
        self.logger.trace(_("Url: %s") % url)
        try:
            parsed = urlparse.urlparse(url)
            domain = parsed.hostname

            ip = socket.gethostbyname(domain)

            matches = all_matching_cidrs(ip, ["10.0.0.0/8", "0.0.0.0/8",
                                              "172.16.0.0/12",
                                              "192.168.0.0/16", "127.0.0.0/8"])

            if matches:
                self.logger.warn(_("Prevented a portscan: %s") % url)
                return None, None

            if domain.startswith("www."):
                domain = domain[4:]

            if use_handler:
                for pattern in self.handlers:
                    if fnmatch.fnmatch(domain, pattern):
                        try:
                            result = self.handlers[domain](url)
                            if result:
                                return to_unicode(result), None
                        except Exception:
                            self.logger.exception(_("Error running handler, "
                                                    "parsing title normally."))

            self.logger.trace(_("Parsed domain: %s") % domain)

            request = urllib2.Request(url)
            if domain in self.spoofing:
                self.logger.debug(_("Custom spoofing for this domain found."))
                user_agent = self.spoofing[domain]
                if user_agent:
                    self.logger.debug(_("Spoofing user-agent: %s")
                                      % user_agent)
                    request.add_header("User-agent", user_agent)
                else:
                    self.logger.debug(_("Not spoofing user-agent."))
            else:
                self.logger.debug(_("Spoofing Firefox as usual."))
                request.add_header('User-agent', 'Mozilla/5.0 (X11; U; Linux '
                                                 'i686; en-US; rv:1.9.0.1) '
                                                 'Gecko/2008071615 Fedora/3.0.'
                                                 '1-1.fc9-1.fc9 Firefox/3.0.1')

            # Deal with Accept-Language
            language_value = None
            language = self.config.get("accept_language", {})
            language_domains = language.get("domains", {})
            if domain in language_domains:
                language_value = language_domains[domain]
            elif domain.lower() in language_domains:
                language_value = language_domains[domain.lower()]
            elif "default" in language:
                language_value = language["default"]

            if language_value is not None:
                request.add_header("Accept-Language", language_value)

            response = urllib2.urlopen(request)

            self.logger.trace(_("Info: %s") % response.info())

            headers = response.info().headers
            new_url = response.geturl()

            _domain = domain

            parsed = urlparse.urlparse(new_url)
            domain = parsed.hostname

            if _domain != domain:
                self.logger.info(_("URL: %s") % new_url)
                self.logger.info(_("Domain: %s") % domain)

                if self.check_blacklist(new_url):
                    self.logger.debug(_("Not parsing, URL is blacklisted."))
                    return

                ip = socket.gethostbyname(domain)

                matches = all_matching_cidrs(ip, ["10.0.0.0/8", "0.0.0.0/8",
                                                  "172.16.0.0/12",
                                                  "192.168.0.0/16",
                                                  "127.0.0.0/8"])

                if matches:
                    self.logger.warn(_("Prevented a portscan: %s") % new_url)
                    return None, None

                if domain.startswith("www."):
                    domain = domain[4:]

                if domain in self.handlers and use_handler:
                    try:
                        result = self.handlers[domain](new_url)
                        if result:
                            return to_unicode(result), None
                    except Exception:
                        self.logger.exception(_("Error running handler,"
                                                " parsing title normally."))

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

            self.logger.trace(_("Content-type: %s") % repr(ct))

            if ct not in self.content_types:
                self.logger.debug(_("Content-type is not allowed."))
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
                self.logger.exception(_("Error parsing title."))
                return str(e), domain
            return None, None

    def _shorten(self, txn, url, handler):
        """
        Shorten a URL, checking the database in case it's already been
        done. This is a database interaction and uses Deferreds.
        """

        txn.execute("SELECT * FROM urls WHERE url=? AND shortener=?",
                    (url, handler.lower()))
        r = txn.fetchone()

        self.logger.trace(_("Result (SQL): %s") % repr(r))

        if r is not None:
            return r[2]

        if handler in self.shorteners:
            result = self.shorteners[handler](url)

            txn.execute("INSERT INTO urls VALUES (?, ?, ?)",
                        (url, handler.lower(), result))
            return result
        return None

    def shorten_url(self, url, handler):
        """
        Shorten a URL using the specified handler. This returns a Deferred.

        :param url: The URL to shorten
        :param handler: The name of the handler to shorten with

        :type url: str
        :type handler: str

        :returns: Deferred which will fire with the result or None
        :rtype: Deferred
        """

        self.logger.trace(_("URL: %s") % url)
        self.logger.trace(_("Handler: %s") % handler)

        return self.shortened.runInteraction(self._shorten, url, handler)

    def add_handler(self, domain, handler):
        """
        API method to add a specialized URL handler.

        This will fail if there's already a handler there for that domain.

        :param domain: The domain to handle, without the 'www.'.
        :param handler: The callable handler

        :type domain: str
        :type handler: callable

        :returns: Whether the handler was registered
        :rtype: bool
        """

        if domain.startswith("www."):
            raise ValueError(_("Domain should not start with 'www.'"))
        if domain not in self.handlers:
            self.logger.trace(_("Handler registered for '%s': %s")
                              % (domain, handler))
            self.handlers[domain] = handler
            return True
        return False

    def add_shortener(self, name, handler):
        """
        API method to add a URL shortener. This is the same as
        `add_handler`, but for URL shortening.
        """

        if name not in self.shorteners:
            self.logger.trace(_("Shortener '%s' registered: %s")
                              % (name, handler))
            self.shorteners[name] = handler
            return True
        return False

    def remove_handler(self, domain):
        if domain.startswith("www."):
            raise ValueError(_("Domain should not start with 'www.'"))
        if domain in self.handlers:
            del self.handlers[domain]
            return True
        return False

    def remove_shortener(self, name):
        if name in self.shorteners:
            del self.shorteners[name]
            return True
        return False
