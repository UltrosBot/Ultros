# coding=utf-8

from kitchen.text.converters import to_unicode
from plugins.urls.matching import REGEX_TYPE

__author__ = 'Gareth Coles'


class URLHandler(object):
    """
    URL handler. Subclass this!

    You'll want to override both the `call` method and the *criteria* dict.
    The former is called if the criteria matches the URL.

    In the criteria dict, you're expected to provide values to test equality
    for. However, there are a few things to be aware of.

    * Leave a key out if you don't care about matching it - None will be
      matched against.
    * You may provide a compiled regular expression to test against as well.
    * Finally, you may provide a callable (function or class), which will be
      run for the comparison instead, and should return either True or False.

    >>> criteria = {
    ...     # No protocol here, since we don't care about it
    ...     "auth": lambda x: x is not None
    ...     "domain": re.compile(u"[a-zA-Z]+"),
    ...     "port": lambda x: x > 8080,
    ...     "path": lambda x: len(x) > 10,
    ...     "permission": "urls.trigger.example"  # If you need one
    ... }
    ...
    >>>

    Additionally, if the above matching is somehow not good enough for you, you
    may override the `match` function.
    """

    # Remember to set this, so that there are no conflicting handlers - only
    # one handler per name!
    name = ""

    plugin = None
    urls_plugin = None

    criteria = {
        "protocol": None,
        "auth": None,
        "domain": None,
        "port": None,
        "path": None,

        # Check the user and source for a permission - This is not a URL field
        "permission": None,
    }

    def __init__(self, plugin):
        """
        Initializer. The plugin here is your plugin, not the URLs plugin.
        You're expected to initialize this object yourself, so feel free to
        override this.
        """

        self.plugin = plugin

    def call(self, url, context):
        """
        Called if the URL matches. Override this or there's basically no point
        in having a handler.

        *context* here is a dict containing "protocol", "source", and "target"
        keys, which you can use to respond to whoever sent the message which
        contained the URL.

        Return True if this should cascade to any other handlers, or False
        if it should end here.

        If an exception is raised, it will be caught and we'll move on to the
        next handler.

        :param url: The URL object that was matched
        :param context: Dictionary with the current context, contains
                        the MessageReceived event under "event" in normal
                        circumstances

        :type url: plugins.urls.url.URL
        :type context: dict

        :return: constants.STOP_HANDLING or constants.CASCADE
        :rtype: int
        """

        raise NotImplementedError()

    def match(self, url, context):
        """
        Decide whether to handle this URL.

        This should return True if this handler should handle the URL, or
        False if not.

        Do not do any actual handling here. You should only override this if
        the built-in handling doesn't cover your needs for some reason.

        :param url: The URL object to match
        :param context: Dictionary with the current context

        :return: True if this handler should handle the URL, False otherwise
        """

        for key in self.criteria.iterkeys():
            value = self.criteria.get(key)

            if key == "permission":
                event = context["event"]
                result = self.plugin.commands.perm_handler.check(
                    value, event.source, event.target, event.caller
                )
                if not result:
                    return False
                continue

            if callable(value):  # Function, lambda, etc
                if value(getattr(url, key)):
                    continue
                else:
                    return False

            elif isinstance(value, REGEX_TYPE):  # Compiled regex
                # Casting due to port, None, etc
                if value.match(to_unicode(getattr(url, key))):
                    continue
                else:
                    return False

            elif value == getattr(url, key):  # Standard equality test
                continue
            else:
                return False

        return True

    def teardown(self):
        """
        Called when the URLs plugin unloads - Do any saving or cleanup you
        need to do here
        """

        pass

    def reload(self):
        """
        Called when the URLs plugin has its configuration reloaded - You are
        free to leave this as it is if it isn't relevant to your plugin
        """

        pass
