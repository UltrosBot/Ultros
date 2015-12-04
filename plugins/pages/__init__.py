# coding=utf-8

"""
A plugin designed to provide command-based pagination to other plugins.

If you need pagination, you should almost definitely use this plugin as
it will ensure that things work as users expect them to work.
"""

__author__ = "Gareth Coles"

from system.plugins.plugin import PluginObject
from system.translations import Translations

__ = Translations().get_m()


class PagesPlugin(PluginObject):
    """
    Pages plugin object
    """

    lines_per_page = 5
    stored_pages = {}

    def setup(self):
        """
        Called when the plugin is loaded. Performs initial setup.
        """

        self.commands.register_command(
            "page", self.page_command, self, default=True
        )

    def send_page(self, pageset, pagenum, target):
        """
        Send a page from a pageset to a specified target.

        :param pageset: The pageset to send
        :param pagenum: The page number
        :param target: The target to send to

        :type pageset: str
        :type pagenum: int
        :type target: User, Channel
        """

        if pageset not in self.stored_pages:
            target.respond(__("No pages found."))
            return

        if pagenum < 1:
            target.respond(__("Page %s not found - the page number must be "
                              "positive.") % pagenum)
            return

        index = pagenum - 1
        numpages = len(self.stored_pages[pageset]) - 1
        if index > numpages:
            target.respond(__("Page %s not found - there are %s pages.") %
                           (pagenum, numpages + 1))
            return

        page = self.stored_pages[pageset][index]

        target.respond(__("== Page %s/%s ==") % (pagenum, numpages + 1))
        for line in page:
            target.respond(line)

        target.respond(__("== Use {CHARS}page <page number> to see more. =="))

    def page(self, pageset, lines):
        """
        Create and store a pageset from a list of lines.

        :param pageset: The pageset to create and store
        :param lines: A list of lines to paginate

        :type pageset: str
        :type lines: list
        """

        pages = []
        current = []

        for line in lines:
            current.append(line)
            if len(current) == self.lines_per_page:
                pages.append(current)
                current = []

        if current:
            pages.append(current)

        self.stored_pages[pageset] = pages

    def get_pageset(self, protocol, target):
        """
        Get the name of a pageset for a given protocol and target.

        :param protocol: The protocol to use
        :param target: The target to use

        :type protocol: Protocol
        :type target: User, Channel

        :return: The name of the pageset
        :rtype: str
        """
        return "%s:%s" % (protocol.name, target.name)

    def page_command(self, protocol, caller, source, command, raw_args,
                     args):
        """
        Command handler for the page command
        """

        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond(__("Usage: {CHARS}%s <page number>" % command))
            return

        pagenum = args[0]

        try:
            pagenum = int(pagenum)
        except Exception:
            source.respond("'%s' is not a number." % pagenum)
            return

        page = self.get_pageset(protocol, source)

        self.send_page(page, pagenum, source)
