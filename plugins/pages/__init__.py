# coding=utf-8
__author__ = "Gareth Coles"

import system.plugin as plugin

from system.command_manager import CommandManager
from system.translations import Translations
# _ = Translations().get()
__ = Translations().get_m()


class PagesPlugin(plugin.PluginObject):
    lines_per_page = 5
    stored_pages = {}

    commands = None

    def setup(self):
        self.commands = CommandManager()
        self.commands.register_command("page", self.page_command, self)

    def send_page(self, pageset, pagenum, target):
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
        return "%s:%s" % (protocol.name, target.name)

    def page_command(self, protocol, caller, source, command, raw_args,
                     args):
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
