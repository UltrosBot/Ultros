"""
Authorization plugin. Handles logins and permissions.

If you want any real control over permissions, you'll need to be using this
plugin. Most plugins don't require it, however, due to the new "default"
commands system.

If you need to work directly with the auth handler or permissions handler,
this is the plugin you want to get from the plugin manager.
"""

__author__ = 'Gareth Coles'

import auth_handler
import permissions_handler

from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.events.general import PreCommand

import system.plugin as plugin

from system.protocols.generic.channel import Channel
from system.storage.formats import YAML
from system.storage.manager import StorageManager

from system.translations import Translations
_ = Translations().get()
__ = Translations().get_m()


class AuthPlugin(plugin.PluginObject):
    """
    Auth plugin. In charge of logins and permissions.
    """

    config = None
    passwords = None
    permissions = None
    blacklist = None

    commands = None
    events = None
    storage = None

    auth_h = None
    perms_h = None

    def setup(self):
        """
        Called when the plugin is loaded. Performs initial setup.
        """

        self.logger.trace(_("Entered setup method."))

        self.storage = StorageManager()
        try:
            self.config = self.storage.get_file(self, "config", YAML,
                                                "plugins/auth.yml")
        except Exception:
            self.logger.exception(_("Error loading configuration!"))
            self.logger.error(_("Disabling.."))
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error(_("Unable to find config/plugins/auth.yml"))
            self.logger.error(_("Disabling.."))
            self._disable_self()
            return

        self.commands = CommandManager()
        self.events = EventManager()

        if self.config["use-permissions"]:
            try:
                self.permissions = self.storage.get_file(self, "data", YAML,
                                                         "plugins/auth/"  # PEP
                                                         "permissions.yml")
            except Exception:
                self.logger.exception(_("Unable to load permissions. They "
                                        "will be unavailable!"))
            else:
                self.perms_h = permissions_handler.permissionsHandler(
                    self, self.permissions)
                result = self.commands.set_permissions_handler(self.perms_h)
                if not result:
                    self.logger.warn(_("Unable to set permissions handler!"))

        if self.config["use-auth"]:
            try:
                self.passwords = self.storage.get_file(self, "data", YAML,
                                                       "plugins/auth/"  # PEP!
                                                       "passwords.yml")
                self.blacklist = self.storage.get_file(self, "data", YAML,
                                                       "plugins/auth/"  # PEP!
                                                       "blacklist.yml")
            except Exception:
                self.logger.exception(_("Unable to load user accounts. They "
                                        "will be unavailable!"))
            else:
                self.auth_h = auth_handler.authHandler(self, self.passwords,
                                                       self.blacklist)
                result = self.commands.add_auth_handler(self.auth_h)
                if not result:
                    self.logger.warn(_("Unable to set auth handler!"))

        self.logger.debug(_("Registering commands."))
        self.commands.register_command("login", self.login_command,
                                       self, "auth.login", default=True)
        self.commands.register_command("logout", self.logout_command,
                                       self, "auth.login", default=True)
        self.commands.register_command("register", self.register_command,
                                       self, "auth.register", default=True)
        self.commands.register_command("passwd", self.passwd_command, self,
                                       "auth.passwd", default=True)

        self.events.add_callback("PreCommand", self, self.pre_command, 10000)

    def pre_command(self, event=PreCommand):
        """
        Pre-command hook to remove passwords from the log output.
        """

        self.logger.trace(_("Command: %s") % event.command)
        if event.command.lower() in ["login", "register"]:
            if len(event.args) >= 2:
                split_ = event.printable.split("%s " % event.command)
                second_split = split_[1].split()
                second_split[1] = _("[REDACTED]")
                split_[1] = " ".join(second_split)
                donestr = "%s " % event.command
                done = donestr.join(split_)
                event.printable = done
        elif event.command.lower() == "passwd":
            split_ = event.printable.split("%s " % event.command)
            second_split = split_[1].split()

            dsplit = []
            for x in second_split:
                dsplit.append(_("[REDACTED]"))

            split_[1] = " ".join(dsplit)
            donestr = "%s " % event.command
            done = donestr.join(split_)
            event.printable = done

    def login_command(self, protocol, caller, source, command, raw_args,
                      parsed_args):
        """
        Command handler for the login command - for logging users in.
        """

        args = raw_args.split()  # Quick fix for new command handler signature
        if len(args) < 2:
            caller.respond(__("Usage: {CHARS}login <username> <password>"))
        else:
            if self.auth_h.authorized(caller, source, protocol):
                caller.respond(__("You're already logged in. "
                                  "Try logging out first!"))
                return
            username = args[0]
            password = args[1]

            result = self.auth_h.login(caller, protocol, username, password)
            if not result:
                self.logger.warn(_("%s failed to login as %s")
                                 % (caller.nickname, username))
                caller.respond(__("Invalid username or password!"))
            else:
                self.logger.info(_("%s logged in as %s")
                                 % (caller.nickname, username))
                caller.respond(__("You are now logged in as %s.")
                               % username)

    def logout_command(self, protocol, caller, source, command, raw_args,
                       parsed_args):
        """
        Command handler for the logout command - for logging users out.
        """

        if self.auth_h.authorized(caller, source, protocol):
            self.auth_h.logout(caller, protocol)
            caller.respond(__("You have been logged out successfully."))
        else:
            caller.respond(__("You're not logged in."))

    def register_command(self, protocol, caller, source, command, raw_args,
                         parsed_args):
        """
        Command handler for the register command - for creating new user
        accounts.
        """

        args = raw_args.split()  # Quick fix for new command handler signature
        if len(args) < 2:
            caller.respond(__("Usage: {CHARS}register <username> <password>"))
            return
        username = args[0]
        password = args[1]

        if isinstance(source, Channel):
            source.respond(__("You can't create an account in a channel."))
            caller.respond(__("Don't use this command in a channel!"))
            caller.respond(__("You should only use it in a private message."))
            caller.respond(__("For your security, the password you used has "
                              "been blacklisted."))
            self.auth_h.blacklist_password(password, username)
            return

        if self.auth_h.user_exists(username):
            caller.respond(__("That username already exists!"))
            return

        if self.auth_h.password_backlisted(password, username):
            caller.respond(__("That password has been blacklisted. "
                              "Try another!"))
            return

        if self.auth_h.create_user(username, password):
            caller.respond(__("Your account has been created and you will now "
                              "be logged in. Thanks for registering!"))
            self.perms_h.create_user(username)
            self.login_command(caller, source, [username, password], protocol,
                               raw_args, parsed_args)
        else:
            caller.respond(__("Something went wrong when creating your "
                              "account! You should ask the bot operators "
                              "about this."))

    def passwd_command(self, protocol, caller, source, command, raw_args,
                       parsed_args):
        """
        Command handler for the passwd command - for changing passwords.
        """

        args = raw_args.split()  # Quick fix for new command handler signature
        if len(args) < 2:
            caller.respond(__("Usage: {CHARS}passwd <old password> "
                              "<new password>"))
            return
        if not self.auth_h.authorized(caller, source, protocol):
            caller.respond(__("You must be logged in to change your "
                              "password."))
            return

        username = caller.auth_name

        old = args[0]
        new = args[1]

        if self.auth_h.password_backlisted(new, username):
            caller.respond(__("That password has been blacklisted. Try "
                              "another!"))
            return

        if self.auth_h.change_password(username, old, new):
            caller.respond(__("Your password has been changed successfully."))
        else:
            caller.respond(__("Old password incorrect - please try again!"))
            self.logger.warn(_("User %s failed to change the password for %s")
                             % (caller, username))

    def get_auth_handler(self):
        """
        API function for getting the auth handler.

        This will return None if the handler is disabled.
        """

        if self.config["use-auth"]:
            return self.auth_h
        return None

    def get_permissions_handler(self):
        """
        API function for getting the permissions handler.

        This will return None if the handler is disabled.
        """
        if self.config["use-permissions"]:
            return self.perms_h
        return None

    def deactivate(self):
        """
        Called when the plugin is deactivated. Does nothing right now.
        """
        pass
