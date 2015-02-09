__author__ = 'Gareth Coles'


class Handler(object):
    """
    URL handler. Subclass this!

    You'll want to override both the `call` method and the *criteria* dict.
    The former is called if the criteria matches the URL.

    In the criteria dict, you're expected to provide values to test equality
    for. However, there are a few things to be aware of.

    * Leave a key out if you don't care about matching it - None will be
      matched against.
    * You can use plugins.urls.utils.notnone.NotNone when you only want to be
      sure something exists.
    * You may provide a compiled regular expression to test against as well.
    * Finally, you may provide a callable (function or class), which will be
      run for the comparison instead, and should return either True or False.

    >>> criteria = {
    ...     # No protocol here, since we don't care about it
    ...     "auth": NotNone,
    ...     "domain": re.compile("[a-zA-Z]+"),
    ...     "port": lambda x: x > 8080,
    ...     "path": lambda x: len(x) > 10
    ... }
    >>>
    """

    plugin = None

    criteria = {
        "protocol": None,
        "auth": None,
        "domain": None,
        "port": None,
        "path": None
    }

    def __init__(self, plugin):
        self.plugin = plugin

    def call(self, url):
        raise NotImplementedError()
