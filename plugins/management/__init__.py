# coding=utf-8

"""Management plugin.

This plugin will allow users to configure and administrate their bots from
the chat networks they're connected to. See the ManagementPlugin docstring
for more information on that.
"""

__author__ = "Gareth Coles"

import system.plugin as plugin

from system.command_manager import CommandManager
from system.constants import *
from system.translations import Translations

from utils.switch import Switch as switch

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
        self.commands.register_command("protocols", self.protocols_command,
                                       self, "management.protocols",
                                       ["pr", "protos", "proto"])
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
        self.commands.register_command("shutdown", self.shutdown_command, self,
                                       "management.shutdown")

    def storage_command(self, protocol, caller, source, command, raw_args,
                        args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond(__("Usage: {CHARS}%s <operation> [params]")
                           % command)
            caller.respond(__("Operations: None yet"))
            # caller.respond("Operations: help, list, [...]")

        operation = args[0]
        caller.respond(__("Unknown operation: %s") % operation)

    def protocols_command(self, protocol, caller, source, command, raw_args,
                          args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond(__("Usage: {CHARS}%s <operation> [params]")
                           % command)
            caller.respond(__("Operations: None yet"))
            # caller.respond("Operations: help, list, [...]")

        operation = args[0]
        for case, default in switch(operation):

            if default:
                caller.respond(__("Unknown operation: %s") % operation)
                break

    def plugins_command(self, protocol, caller, source, command, raw_args,
                        args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond(__("Usage: {CHARS}%s <operation> [params]")
                           % command)
            caller.respond(
                __("Operations: help, info, list, load, reload, unload")
            )
            return

        operation = args[0]

        for case, default in switch(operation):
            if case("help"):
                lines = [
                    __(  # Yey, PEP
                        "{CHARS}%s <operation> [params] - the plugin "
                        "management command. Operations:" % command
                    ),
                    __("> help - This help"),
                    __("> info <plugin> - Get information on an available "
                       "plugin"),
                    __("> list - List all available plugins"),
                    __("> load <plugin> - Load a plugin that's available"),
                    __(  # Yeeeeeey, PEP
                        "> reload <plugin> - Reload a plugin that's already "
                        "loaded"
                    ),
                    __("> unload <plugin> - Unload a currently-loaded plugin"),
                ]

                pageset = self.pages.get_pageset(protocol, source)
                self.pages.page(pageset, lines)
                self.pages.send_page(pageset, 1, source)

                break
            if case("info"):
                if len(args) < 2:
                    caller.respond(__("Usage: {CHARS}%s info <plugin>")
                                   % command)
                    return

                name = args[1]
                plug = self.factory_manager.plugman.getPluginByName(name)

                if plug is None:
                    source.respond(__("Unknown plugin: %s") % name)
                    return

                source.respond(  # Fucking PEP8
                    "%s v%s (%s): %s" % (
                        plug.name, plug.version, plug.author, (
                            __("Loaded") if plug.name in
                            self.factory_manager.loaded_plugins
                            else __("Unloaded"))
                    ))

                source.respond("> %s" % plug.description)
                source.respond(__("Website: %s") % plug.website)

                break
            if case("list"):
                self.factory_manager.collect_plugins()
                plugs = self.factory_manager.plugman.getAllPlugins()
                done = {}
                lines = []

                for info in plugs:
                    name = info.name
                    done["%s v%s" % (name, info.version)] = (
                        name in self.factory_manager.loaded_plugins
                    )

                for key in sorted(done.keys()):
                    if done[key]:
                        lines.append(__("%s: Loaded") % key)
                    else:
                        lines.append(__("%s: Unloaded") % key)

                pageset = self.pages.get_pageset(protocol, source)
                self.pages.page(pageset, lines)
                self.pages.send_page(pageset, 1, source)

                break
            if case("load"):
                if len(args) < 2:
                    caller.respond(__("Usage: {CHARS}%s load <plugin>")
                                   % command)
                    return

                name = args[1]
                result = self.factory_manager.load_plugin(name)

                if result == PLUGIN_ALREADY_LOADED:
                    source.respond(__("Unable to load plugin %s: The plugin "
                                      "is already loaded.") % name)
                elif result == PLUGIN_NOT_EXISTS:
                    source.respond(__("Unknown plugin: %s") % name)
                elif result == PLUGIN_LOAD_ERROR:
                    source.respond(__("Unable to load plugin %s: An error "
                                      "occurred.") % name)
                elif result == PLUGIN_DEPENDENCY_MISSING:
                    source.respond(__("Unable to load plugin %s: Another "
                                      "plugin this one depends on is "
                                      "missing.") % name)
                elif result == PLUGIN_LOADED:
                    source.respond(__("Loaded plugin: %s") % name)
                else:  # THIS SHOULD NEVER HAPPEN
                    source.respond(__("Error while loading plugin %s: Unknown "
                                      "return code %s") % (name, result))

                break
            if case("reload"):
                if len(args) < 2:
                    caller.respond(__("Usage: {CHARS}%s reload <plugin>")
                                   % command)
                    return

                name = args[1]

                plug = self.factory_manager.plugman.getPluginByName(name)

                if plug is None:
                    source.respond(__("Unknown plugin: %s") % name)
                    return

                if name not in self.factory_manager.loaded_plugins:
                    source.respond(__("Unable to reload plugin %s: The plugin "
                                      "is not loaded.") % name)
                    return

                result = self.factory_manager.load_plugin(name, unload=True)

                if result == PLUGIN_NOT_EXISTS:
                    source.respond(__("Unknown plugin: %s") % name)
                elif result == PLUGIN_LOAD_ERROR:
                    source.respond(__("Unable to reload plugin %s: An error "
                                      "occurred.") % name)
                elif result == PLUGIN_DEPENDENCY_MISSING:
                    source.respond(__("Unable to reload plugin %s: Another "
                                      "plugin this one depends on is missing.")
                                   % name)
                elif result == PLUGIN_LOADED:
                    source.respond(__("Reloaded plugin: %s") % name)
                else:  # THIS SHOULD NEVER HAPPEN
                    source.respond(__("Error while reloading plugin %s: "
                                      "Unknown return code %s")
                                   % (name, result))

                break
            if case("unload"):
                if len(args) < 2:
                    caller.respond(__("Usage: {CHARS}%s unload <plugin>")
                                   % command)
                    return

                name = args[1]

                plug = self.factory_manager.plugman.getPluginByName(name)

                if plug is None:
                    source.respond(__("Unknown plugin: %s") % name)
                    return

                if name not in self.factory_manager.loaded_plugins:
                    source.respond(__("Unable to unload plugin %s: The plugin "
                                      "is not loaded.") % name)
                    return

                result = self.factory_manager.unload_plugin(name)

                if result == PLUGIN_NOT_EXISTS:
                    source.respond(__("Unknown plugin: %s") % name)
                elif result == PLUGIN_UNLOADED:
                    source.respond(__("Unloaded plugin: %s") % name)
                else:  # THIS SHOULD NEVER HAPPEN
                    source.respond(__("Error while loading plugin %s: Unknown "
                                      "return code %s") % (name, result))

                break
            if default:
                caller.respond(__("Unknown operation: %s") % operation)

    def packages_command(self, protocol, caller, source, command, raw_args,
                         args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond(__("Usage: {CHARS}%s <operation> [params]")
                           % command)
            caller.respond(__("Operations: None yet"))
            # caller.respond("Operations: help, list, [...]")

        operation = args[0]
        caller.respond(__("Unknown operation: %s") % operation)

    def permissions_command(self, protocol, caller, source, command, raw_args,
                            args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond(__("Usage: {CHARS}%s <operation> [params]")
                           % command)
            caller.respond(__("Operations: None yet"))
            # caller.respond("Operations: help, list, [...]")

        operation = args[0]
        caller.respond(__("Unknown operation: %s") % operation)

    def users_command(self, protocol, caller, source, command, raw_args,
                      args):
        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond(__("Usage: {CHARS}%s <operation> [params]")
                           % command)
            caller.respond(__("Operations: None yet"))
            # caller.respond("Operations: help, list, [...]")

        operation = args[0]
        caller.respond(__("Unknown operation: %s") % operation)

    def shutdown_command(self, protocol, caller, source, command, raw_args,
                         args):
        self.factory_manager.unload()
