# coding=utf-8

__author__ = 'Gareth Coles'


class Shortener(object):
    # Remember to set this, so that your shortener can be identified!
    name = ""

    plugin = None
    urls_plugin = None

    def __init__(self, plugin):
        self.plugin = plugin

    def do_shorten(self, context):
        """
        Take a context dict and return a Deferred that results in the shortened
        URL, or another Deferred which itself returns a URL.
        """

        pass

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
