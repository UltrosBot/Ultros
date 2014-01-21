# coding=utf-8
import shlex

__author__ = "Gareth Coles"

import logging

from system.decorators import Singleton
from system.plugin import PluginObject
from utils.log import getLogger
from utils.misc import output_exception


@Singleton
class CommandManager(object):
    """
    This is the command manager. It's in charge of tracking commands that
    plugins wish to offer, and providing ways for plugins to offer methods
    of providing authentication and permissions.
    """

    commands = {}
    auth_handlers = []
    perm_handler = None
    factory_manager = None

    # commands = {
    #   "command": {
    #     "f": func(),
    #     "permission": "plugin.command",
    #     "owner": Name of plugin, or an instance of a class
    #   }
    # }

    def __init__(self):
        self.logger = getLogger("Commands")

    @staticmethod
    def instance(self=None):
        """
        This only exists to help developers using decent IDEs.
        Don't actually use it.
        """
        if self is None:
            self = CommandManager
        return self

    def set_factory_manager(self, factory_manager):
        """
        Set the factory manager. This should only ever be called by the
        factory manager itself.
        """
        self.factory_manager = factory_manager

    def register_command(self, command, handler, owner, permission=None):
        """
        Register a command, provided it hasn't been registered already.
        The params should go like this..

        :param command - A string, the command
        :param handler - A function to handle the command
        :param owner - The plugin registering the command
        :param permission (optional) - The permission needed to run the command

        :returns True/False based on whether the command was registered or not
        """
        if command in self.commands:
            self.logger.warn("Plugin '%s' tried to register command '%s' but"
                             "it's already been registered by plugin '%s'."
                             % (
                                 command,
                                 self.commands[command]["owner"].info.name,
                                 owner.info.name
                             ))
            return False
        self.logger.debug("Registering command: %s (%s)"
                          % (command, owner.info.name))
        self.commands[command] = {
            "f": handler,
            "permission": permission,
            "owner": owner.info.name if (owner, PluginObject) else owner
        }
        return True

    def unregister_commands_for_owner(self, owner):
        current = self.commands.items()
        if isinstance(owner, PluginObject):
            owner = owner.info.name
        for key, value in current:
            if owner == value["owner"]:
                del self.commands[key]
                self.logger.debug("Unregistered command: %s" % key)

    def run_command(self, command, caller, source, protocol, args):
        """
        Run a command, provided it's been registered.

        :param command - The command, a string
        :param caller - Who ran the command
        :param source - Where they ran the command
        :param protocol - The protocol they're part of
        :param args - A list of arguments for the command

        :return (False, None) if the command isn't registered
                (False, True) if we couldn't authorize the user for the command
                (False, Exception) if an error happened while running
                (True, None) if the command was run successfully
        """
        if not command in self.commands:
            return False, None
        # Parse args
        raw_args = args
        try:
            lex = shlex.shlex(args, posix=True)
            lex.whitespace_split = True
            lex.quotes = '"'
            lex.commenters = ""
            parsed_args = list(lex)
        except ValueError:
            parsed_args = None
        try:
            if self.commands[command]["permission"]:
                if not self.perm_handler or not self.auth_handlers:
                    return False, True
                else:
                    authorized = False
                    for handler in self.auth_handlers:
                        if handler.authorized(caller, source, protocol):
                            authorized = True
                            break

                    if authorized:
                        if self.perm_handler.check(self.commands
                                                   [command]["permission"],
                                                   caller, source, protocol):
                            try:
                                self.commands[command]["f"](protocol, caller,
                                                            source, command,
                                                            raw_args,
                                                            parsed_args)
                            except Exception as e:
                                output_exception(self.logger, logging.DEBUG)
                                return False, e
                        else:
                            return False, True
                    else:
                        if self.perm_handler.check(self.commands
                                                   [command]["permission"],
                                                   None, source, protocol):
                            try:
                                self.commands[command]["f"](protocol, caller,
                                                            source, command,
                                                            raw_args,
                                                            parsed_args)
                            except Exception as e:
                                output_exception(self.logger, logging.DEBUG)
                                return False, e
                        else:
                            return False, True
            else:
                self.commands[command]["f"](protocol, caller, source, command,
                                            raw_args, parsed_args)
        except Exception as e:
            output_exception(self.logger, logging.ERROR)
            return False, e
        else:
            return True, None

    def add_auth_handler(self, handler):
        """
        Add an auth handler, provided it hasn't already been added.

        :param handler - An instance of the handler to add
        :return True/False based on whether the handler was added or not
        """
        for instance in self.auth_handlers:
            if isinstance(instance, handler.__class__):
                self.logger.warn("Auth handler %s is already registered."
                                 % handler)
                return False

        self.auth_handlers.append(handler)
        return True

    def set_permissions_handler(self, handler):
        """
        Set the permissions handler, provided one hasn't already been set.

        :param handler - The instance of the handler to set
        :return True/False based on whether the handler was added or not
        """
        if self.perm_handler:
            self.logger.warn("Two plugins are trying to provide permissions "
                             "handlers. Only the first will be used!")
            return False
        self.perm_handler = handler
        return True
