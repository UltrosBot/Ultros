# coding=utf-8
import shlex

__author__ = "Gareth Coles"

import logging

from system.plugin import PluginObject
from system.singleton import Singleton
from utils.log import getLogger
from utils.misc import output_exception


class CommandManager(object):
    """
    This is the command manager. It's in charge of tracking commands that
    plugins wish to offer, and providing ways for plugins to offer methods
    of providing authentication and permissions.
    """

    __metaclass__ = Singleton

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

        :param command: The command to register
        :param handler: The command handler
        :param owner: The plugin registering the command
        :param permission: The permission needed to run the command

        :type command: str
        :type handler: function
        :type owner: PluginObject
        :type permission: str

        :returns: Whether the command was registered or not
        :rtype: Boolean
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

        This could return one of the following:

        * (False, None) if the command isn't registered
        * (False, True) if the command is registered but the user isn't allowed
          to run it
        * (False, Exception) if an error occurred while running the command
        * (True, None) if the command was run successfully

        :param command: The command, a string
        :param caller: Who ran the command
        :param source: Where they ran the command
        :param protocol: The protocol they're part of
        :param args: A list of arguments for the command

        :type command: str
        :type caller: PluginObject
        :type source: User
        :type protocol: Protocol
        :type args: list

        :rtype: Tuple of (Boolean, [None, Exception or Boolean))
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

        :param handler: The handler to add

        :type handler: object

        :returns: Whether the handler was added or not

        :rtype: Boolean
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

        :param handler: The handler to set

        :type handler: object

        :returns: Whether the handler was set or not

        :rtype: Boolean
        """
        if self.perm_handler:
            self.logger.warn("Two plugins are trying to provide permissions "
                             "handlers. Only the first will be used!")
            return False
        self.perm_handler = handler
        return True
