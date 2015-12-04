# coding=utf-8

"""
Management plugin.

This plugin will allow users to configure and administrate their bots from
the chat networks they're connected to. See the ManagementPlugin docstring
for more information on that.
"""

from system.enums import PluginState  # , ProtocolState
from system.plugins.plugin import PluginObject
from system.translations import Translations

__author__ = "Gareth Coles"

_ = Translations().get()
__ = Translations().get_m()


class ManagementPlugin(PluginObject):
    """
    A plugin designed for on-the-fly management and configuration.

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

    @property
    def pages(self):
        return self.factory_manager.plugman.get_plugin("Pages")

    def setup(self):
        """
        Called when the plugin is loaded. Performs initial setup.
        """

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
        """
        Command handler for the storage command
        """

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
        """
        Command handler for the protocols command
        """

        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond(__("Usage: {CHARS}%s <operation> [params]")
                           % command)
            caller.respond(__("Operations: None yet"))
            # caller.respond("Operations: help, list, load, unload, reload")

        operation = args[0]
        caller.respond(__("Unknown operation: %s") % operation)

    def plugins_command(self, protocol, caller, source, command, raw_args,
                        args):
        """
        Command handler for the plugins command
        """

        if args is None:
            args = raw_args.split()

        if len(args) < 1:
            caller.respond(__("Usage: {CHARS}%s <operation> [params]")
                           % command)
            caller.respond(
                __("Operations: help, info, list, load, reload, unload")
            )
            return

        operation = args[0].lower()

        if operation == "help":
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

            page_set = self.pages.get_pageset(protocol, source)
            self.pages.page(page_set, lines)
            self.pages.send_page(page_set, 1, source)
        elif operation == "info":
            if len(args) < 2:
                caller.respond(__("Usage: {CHARS}%s info <plugin>")
                               % command)
                return

            name = args[1]
            plug = self.factory_manager.plugman.get_plugin_info(name)

            if plug is None:
                source.respond(__("Unknown plugin: %s") % name)
                return

            source.respond(  # Fucking PEP8
                "%s v%s (%s): %s" % (
                    plug.name, plug.version, plug.author, (
                        __("Loaded") if
                        self.factory_manager.plugman.plugin_loaded(plug.name)
                        is not None else __("Unloaded"))
                ))

            source.respond("> %s" % plug.description)
            source.respond(__("Website: %s") % plug.website)
        elif operation == "list":
            self.factory_manager.plugman.scan()
            done = {}
            lines = []

            for info in self.factory_manager.plugman.info_objects.values():
                done["%s v%s" % (info.name, info.version)] = (
                    self.factory_manager.plugman.plugin_loaded(info.name)
                )

            for key in sorted(done.keys()):
                if done[key]:
                    lines.append(__("%s: Loaded") % key)
                else:
                    lines.append(__("%s: Unloaded") % key)

            page_set = self.pages.get_pageset(protocol, source)
            self.pages.page(page_set, lines)
            self.pages.send_page(page_set, 1, source)
        elif operation == "load":
            if len(args) < 2:
                caller.respond(__("Usage: {CHARS}%s load <plugin>")
                               % command)
                return

            self.factory_manager.plugman.scan()

            name = args[1]
            result = self.factory_manager.plugman.load_plugin(name)
            info = self.factory_manager.plugman.get_plugin_info(name)

            if result is PluginState.AlreadyLoaded:
                source.respond(__("Unable to load plugin %s: The plugin "
                                  "is already loaded.") % info.name)
            elif result is PluginState.NotExists:
                source.respond(__("Unknown plugin: %s") % name)
            elif result is PluginState.LoadError:
                source.respond(__("Unable to load plugin %s: An error "
                                  "occurred.") % info.name)
            elif result is PluginState.DependencyMissing:
                source.respond(__("Unable to load plugin %s: Another "
                                  "plugin this one depends on is "
                                  "missing.") % info.name)
            elif result is PluginState.Loaded:
                source.respond(__("Loaded plugin: %s") % info.name)
            elif result is PluginState.Unloaded:
                source.respond(__("Unloaded plugin: %s") % info.name)
                source.respond(__("This means the plugin disabled itself!"))
            else:  # THIS SHOULD NEVER HAPPEN
                source.respond(__("Error while loading plugin %s: Unknown "
                                  "return code %s") % (name, result))
        elif operation == "reload":
            if len(args) < 2:
                caller.respond(__("Usage: {CHARS}%s reload <plugin>")
                               % command)
                return

            name = args[1]

            result = self.factory_manager.plugman.reload_plugin(name)
            info = self.factory_manager.plugman.get_plugin_info(name)

            if result is PluginState.NotExists:
                source.respond(__("Unknown plugin or plugin not loaded: "
                                  "%s") % name)
            elif result is PluginState.LoadError:
                source.respond(__("Unable to reload plugin %s: An error "
                                  "occurred.") % info.name)
            elif result is PluginState.DependencyMissing:
                source.respond(__("Unable to reload plugin %s: Another "
                                  "plugin this one depends on is missing.")
                               % info.name)
            elif result is PluginState.Loaded:
                source.respond(__("Reloaded plugin: %s") % info.name)
            elif result is PluginState.Unloaded:
                source.respond(__("Unloaded plugin: %s") % info.name)
                source.respond(__("This means the plugin disabled itself!"))
            else:  # THIS SHOULD NEVER HAPPEN
                source.respond(__("Error while reloading plugin %s: "
                                  "Unknown return code %s")
                               % (name, result))
        elif operation == "unload":
            if len(args) < 2:
                caller.respond(__("Usage: {CHARS}%s unload <plugin>")
                               % command)
                return

            name = args[1]

            result = self.factory_manager.plugman.unload_plugin(name)
            info = self.factory_manager.plugman.get_plugin_info(name)

            if result is PluginState.NotExists:
                source.respond(__("Unknown plugin: %s") % name)
            elif result is PluginState.Unloaded:
                source.respond(__("Unloaded plugin: %s") % info.name)
            else:  # THIS SHOULD NEVER HAPPEN
                source.respond(__("Error while loading plugin %s: Unknown "
                                  "return code %s") % (name, result))
        else:
            caller.respond(__("Unknown operation: %s") % operation)

    def packages_command(self, protocol, caller, source, command, raw_args,
                         args):
        """
        Command handler for the packages command
        """

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
        """
        Command handler for the permissions command
        """

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
        """
        Command handler for the users command
        """

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
        """
        Command handler for the shutdown command
        """

        self.factory_manager.unload()
