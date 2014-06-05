# coding=utf-8
__author__ = "Gareth Coles"

import system.plugin as plugin

from system.command_manager import CommandManager
from system.translations import Translations

_ = Translations().get()
__ = Translations().get_m()


class ManagementPlugin(plugin.PluginObject):
    """
    This plugin has a few goals..

    * Storage management
        * Allow listing of files and their owners
        * Allow reloading of specific files
        * Allow reloading of files for a specific owner
    * Plugin management
        * Allow listing of plugins (available and loaded)
        * Allow plugin loading, reloading and unloading
        * Allow retrieval of plugin information
    * Package management
        * Allow listing of packages (available and installed)
        * Allow package installation and removal
        * Allow retrieval of package information
        * Cache list of packages for speed, configurable interval
    * Permissions management
        * Allow listing of permissions in all contexts
            * Point out where they come from
        * Allow addition and removal of permissions in all contexts
        * Allow listing and setting options on users and groups
    * User management
        * Allow listing of users and password resets
        * Allow management of blacklisted passwords
    """

    commands = None

    #: :type: PagesPlugin
    pages = None

    def setup(self):
        self.commands = CommandManager()

        #: :type: PagesPlugin
        self.pages = self.factory_manager.get_plugin("Pages")

        self.commands.register_command("storage", self.storage_command, self,
                                       "management.storage",
                                       ["st", "files", "file"])
        self.commands.register_command("plugins", self.plugins_command, self,
                                       "management.plugins",
                                       ["pl", "plugs", "plug"])
        self.commands.register_command("packages", self.packages_command, self,
                                       "management.packages",
                                       ["pa", "packs", "pack"])
        self.commands.register_command("permissions", self.permissions_command,
                                       self, "management.permissions",
                                       ["pe", "perms", "perm"])
        self.commands.register_command("users", self.users_command, self,
                                       "management.users",
                                       ["us", "user"])

    def storage_command(self, protocol, caller, source, command, raw_args,
                        args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond("Usage: {CHARS}%s <operation> [params]" % command)
            caller.respond("Operations: None yet")
            # caller.respond("Operations: help, list, [...]")

        operation = args[0]
        caller.respond("Unknown operation: %s" % operation)

    def plugins_command(self, protocol, caller, source, command, raw_args,
                        args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond("Usage: {CHARS}%s <operation> [params]" % command)
            caller.respond("Operations: list")
            # caller.respond("Operations: help, list, load, reload, unload")
            return

        operation = args[0]

        if operation == "list":
            plugs = self.factory_manager.plugman.getAllPlugins()
            done = {}
            lines = []

            for info in plugs:
                name = info.name
                done[name] = name in self.factory_manager.loaded_plugins

            for key in sorted(done.keys()):
                if done[key]:
                    lines.append("%s: Loaded" % key)
                else:
                    lines.append("%s: Unloaded" % key)

            pageset = self.pages.get_pageset(protocol, source)
            self.pages.page(pageset, lines)

            self.pages.send_page(pageset, 1, source)
        else:
            caller.respond("Unknown operation: %s" % operation)

    def packages_command(self, protocol, caller, source, command, raw_args,
                         args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond("Usage: {CHARS}%s <operation> [params]" % command)
            caller.respond("Operations: None yet")
            # caller.respond("Operations: help, list, [...]")

        operation = args[0]
        caller.respond("Unknown operation: %s" % operation)

    def permissions_command(self, protocol, caller, source, command, raw_args,
                            args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond("Usage: {CHARS}%s <operation> [params]" % command)
            caller.respond("Operations: None yet")
            # caller.respond("Operations: help, list, [...]")

        operation = args[0]
        caller.respond("Unknown operation: %s" % operation)

    def users_command(self, protocol, caller, source, command, raw_args,
                      args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond("Usage: {CHARS}%s <operation> [params]" % command)
            caller.respond("Operations: None yet")
            # caller.respond("Operations: help, list, [...]")

        operation = args[0]
        caller.respond("Unknown operation: %s" % operation)
