__author__ = 'Gareth Coles'

import auth_handler
import permissions_handler

from system.command_manager import CommandManager
from system.plugin import PluginObject
from utils.config import Config
from utils.data import Data


class AuthPlugin(PluginObject):

    config = None
    passwords = None
    permissions = None

    commands = None

    auth_h = None
    perms_h = None

    def setup(self):
        self.logger.debug("Entered setup method.")
        try:
            self.config = Config("plugins/auth.yml")
        except Exception:
            self.logger.exception("Error loading configuration!")
            self.logger.error("Disabling..")
            self._disable_self()
            return
        if not self.config.exists:
            self.logger.error("Unable to find config/plugins/auth.yml")
            self.logger.error("Disabling..")
            self._disable_self()
            return

        self.commands = CommandManager.instance()

        if self.config["use-permissions"]:
            try:
                self.permissions = Data("plugins/auth/permissions.yml")
            except Exception:
                self.logger.exception("Unable to load permissions. They will "
                                      "be unavailable!")
            else:
                self.perms_h = permissions_handler.permissionsHandler(
                    self, self.permissions)
                result = self.commands.set_permissions_handler(self.perms_h)
                if not result:
                    self.logger.warn("Unable to set permissions handler!")

        if self.config["use-auth"]:
            try:
                self.passwords = Data("plugins/auth/passwords.yml")
            except Exception:
                self.logger.exception("Unable to load user accounts. They will"
                                      " be unavailable!")
            else:
                self.auth_h = auth_handler.authHandler(self, self.passwords)
                result = self.commands.add_auth_handler(self.auth_h)
                if not result:
                    self.logger.warn("Unable to set auth handler!")

        self.logger.debug("Registering commands.")
        self.commands.register_command("login", self.login_command,
                                       self, "auth.login")
        self.commands.register_command("logout", self.logout_command,
                                       self, "auth.login")

    def login_command(self, caller, source, args, protocol):
        if len(args) < 2:
            caller.respond("Usage: {CHARS}login <username> <password>")
        else:
            if self.auth_h.authorized(caller, source, protocol):
                caller.respond("You're already logged in. "
                               "Try logging out first!")
                return
            username = args[0]
            password = args[1]

            result = self.auth_h.login(caller, protocol, username, password)
            if not result:
                self.logger.warn("%s failed to login as %s" % (caller.nickname,
                                                               username))
                caller.respond("Invalid username or password!")
            else:
                self.logger.info("%s logged in as %s" % (caller.nickname,
                                                         username))
                caller.respond("You are now logged in as %s" % username)

    def logout_command(self, caller, source, args, protocol):
        pass

    def get_auth_handler(self):
        if self.config["use-auth"]:
            return self.auth_h
        return None

    def get_permissions_handler(self):
        if self.config["use-permissions"]:
            return self.perms_h
        return None

    def deactivate(self):
        pass
