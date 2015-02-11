__author__ = 'Gareth Coles'

import re


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
    ...     "domain": re.compile("[a-zA-Z]+"),
    ...     "port": lambda x: x > 8080,
    ...     "path": lambda x: len(x) > 10
    ... }
    ...
    >>>

    Additionally, if the above matching is somehow not good enough for you, you
    may override the `match` function.
    """

    # Apparently, different implementations use different base classes,
    # so this is how we should do this.
    # I've been told hasattr(obj, "match") would work too, but, well, this
    # feels like too much of a kludge, even for me. Plus, there are other
    # objects that have a "match" function.

    __REGEX_TYPE = type(re.compile(""))

    plugin = None
    urls_plugin = None

    criteria = {
        "protocol": None,
        "auth": None,
        "domain": None,
        "port": None,
        "path": None
    }

    def __init__(self, plugin):
        """
        Initializer. The plugin here is your plugin, not the URLs plugin.
        You're expected to initialize this object yourself, so feel free to
        override this.
        """

        self.plugin = plugin

    def call(self, url):
        """
        Called if the URL matches. Override this or there's basically no point
        in having a handler.

        Return True if this should cascade to any other handlers, or False
        if it should end here.

        If an exception is raised, it will be caught and we'll move on to the
        next handler.

        :param url: The URL object that was matched
        :return: True to cascade to other handlers, False otherwise
        """

        raise NotImplementedError()

    def match(self, url):
        """
        Decide whether to handle this URL.

        This should return True if this handler should handle the URL, or
        False if not.

        Do not do any actual handling here. You should only override this if
        the built-in handling doesn't cover your needs for some reason.

        :param url: The URL object to match
        :return: True if this handler should handle the URL, False otherwise
        """

        for key in self.criteria.iterkeys():
            value = self.criteria.get(key)

            if callable(value):  # Function, lambda, etc
                if value(getattr(url, key)):
                    continue
                else:
                    return False

            elif isinstance(value, self.__REGEX_TYPE):  # Compiled regex
                # Casting due to port, None, etc
                if value.match(unicode(getattr(url, key))):
                    continue
                else:
                    return False

            elif value == getattr(url, key):  # Standard equality test
                continue
            else:
                return False

        return True
