# coding=utf-8
from system.commands.exceptions import UsageError, NoPermissionError, \
    CommandError

__author__ = "Gareth Coles"

import shlex

from system.decorators.log import deprecated
from system.decorators.ratelimit import RateLimitExceededError
from system.enums import CommandState
from system.events import general as events
from system.events.manager import EventManager
from system.logging.logger import getLogger
from system.singleton import Singleton
from system.translations import Translations
_ = Translations().get()


class CommandManager(object):
    """This is the command manager. It's in charge of tracking commands that
    plugins wish to offer, and providing ways for plugins to offer methods
    of providing authentication and permissions.
    """

    __metaclass__ = Singleton

    #: Storage for all the registered commands. ::
    #:
    #:     commands = {
    #:         "command": {
    #:             "f": func(),
    #:             "permission": "plugin.command",
    #:             "owner": object
    #:         }
    #:     }
    commands = {}

    #: Storage for command aliases.
    #:
    #:     aliases = {
    #:         "alias": "command"
    #:     }
    aliases = {}

    @property
    @deprecated("Use the singular auth_handler instead")
    def auth_handlers(self):
        if self.auth_handler:
            return [self.auth_handler]
        return []

    #: Storage for all the registered auth handler.
    #:
    #: Auth handlers are in charge of asserting whether users are logged in
    #: or not, and identifying who they are logged in as.
    auth_handler = None

    #: Storage for the permissions handler. There may only ever be one of
    #: these.
    #:
    #: Permissions handlers are in charge of asserting whether a user has
    #: permission for a specified action. They work together with auth
    #: handlers to determine this.
    #: :type: plugins.auth.permissions_handler.permissionsHandler
    perm_handler = None

    #: Storage for the factory manager, to avoid function call overhead.
    factory_manager = None

    def __init__(self):
        self.logger = getLogger("Commands")
        self.event_manager = EventManager()

    def set_factory_manager(self, factory_manager):
        """Set the factory manager.

        This should only ever be called by the factory manager itself.

        :param factory_manager: The factory manager
        :type factory_manager: Manager
        """
        self.factory_manager = factory_manager

    def register_command(self, command, handler, owner, permission=None,
                         aliases=None, default=False):
        """Register a command, provided it hasn't been registered already.

        The params should go like this.

        :param command: The command to register
        :param handler: The command handler
        :param owner: The plugin or object registering the command
        :param permission: The permission needed to run the command
        :param aliases: A list of aliases for the command being registered.
        :param default: Whether the command should be run when there is no
            permissions manager installed.

        :type command: str
        :type handler: function
        :type owner: PluginObject
        :type permission: str, None
        :type aliases: list, None
        :type default: bool

        :returns: Whether the command was registered or not
        :rtype: Boolean
        """

        if aliases is None:
            aliases = []

        if command in self.commands:
            self.logger.warn(_("Object '%s' tried to register command '%s' but"
                               " it's already been registered by object '%s'.")
                             % (owner,
                                command,
                                self.commands[command]["owner"])
                             )
            return False

        self.logger.debug(_("Registering command: %s (%s)")
                          % (command, owner))
        commandobj = {
            "f": handler,
            "permission": permission,
            "owner": owner,
            "default": default
        }

        self.commands[command] = commandobj

        for alias in aliases:
            if alias in self.aliases:
                self.logger.warn(_("Failed to register command alias '%s' as "
                                   "it already belongs to another command.")
                                 % alias)
                continue

            self.logger.debug(_("Registering alias: %s -> %s (%s)")
                              % (alias, command, owner))
            self.aliases[alias] = command

        return True

    def unregister_commands_for_owner(self, owner):
        """Unregister all commands that have been registered by a certain
        object.

        This method checks instances, not types!

        :param owner: The owner to check for
        :type owner: object
        """
        current = self.commands.items()
        for key, value in current:
            if owner is value["owner"]:
                del self.commands[key]
                self.logger.debug(_("Unregistered command: %s") % key)

                aliases = self.aliases.items()
                for k, v in aliases:
                    if v == key:
                        del self.aliases[k]
                        self.logger.debug(_("Unregistered alias: %s") % k)

    def handle_input(self, in_str, caller, source, protocol,
                     control_char=None, our_name=None):
        """Process a set of inputs, to check if there's a command there,
        action it, and give user feedback.

        This is designed to be used from a protocol and is a wrapper for
        process_input.

        :param in_str: The entire message to parse
        :param caller: The User that sent the message
        :param source: The User or Channel that the message was sent to
        :param protocol: The Protocol object the User belongs to
        :param control_char: The control characters (prefix)
        :param our_name: The name of the bot on Protocol

        :type in_str: str
        :type caller: User
        :type source: User, Channel
        :type protocol: Protocol
        :type control_char: str
        :type our_name: str

        :return: Tuple containing CommandState representing the state of
            the command, and either None or an Exception.
        :rtype: tuple(CommandState, None or Exception)
        """
        state, err = self.process_input(in_str, caller, source, protocol,
                                        control_char, our_name)

        if state == CommandState.NotACommand:
            self.logger.debug("Not a command")
        elif state == CommandState.RateLimited:
            self.logger.debug("Command rate-limited")
            caller.respond("That command has been rate-limited,"
                           " please try again later.")
        elif state == CommandState.UnknownOverridden:
            self.logger.debug("Unknown command overridden")
        elif state == CommandState.Unknown:
            self.logger.debug("Unknown command")
        elif state == CommandState.Success:
            self.logger.debug("Command ran successfully")
        elif state == CommandState.NoPermission:
            if self.perm_handler and self.perm_handler.check(
                    "ultros.send_permission_error", caller, source, protocol):
                caller.respond("You don't have permission to run that command.")  # noqa
            msg = "No permission to run command"
            if err and err.permission:
                self.logger.debug('No permission to run command - '
                                  'requires "%s" permission' % err.permission)
            else:
                self.logger.debug("No permission to run command")
        elif state == CommandState.Error:
            caller.respond("Error running command")
        elif state == CommandState.UserVisibleError:
            if err and err.message:
                caller.respond("Error running command: %s" % err.message)
            else:
                caller.respond("Error running command")
        elif state == CommandState.InvalidUsage:
            if err and err.usage:
                caller.respond("Usage: %s" % err.message)
            else:
                caller.respond("Invalid usage")
        else:
            self.logger.debug("Unknown command state: %s" % state)

        return (state != CommandState.NotACommand), state, err

    def process_input(self, in_str, caller, source, protocol,
                      control_char=None, our_name=None):
        """Process a set of inputs, to check if there's a command there and
        action it.

        This is designed to be used from a protocol.

        :param in_str: The entire message to parse
        :param caller: The User that sent the message
        :param source: The User or Channel that the message was sent to
        :param protocol: The Protocol object the User belongs to
        :param control_char: The control characters (prefix)
        :param our_name: The name of the bot on Protocol

        :type in_str: str
        :type caller: User
        :type source: User, Channel
        :type protocol: Protocol
        :type control_char: str
        :type our_name: str

        :return: Tuple containing CommandState representing the state of
            the command, and either None or an Exception.
        :rtype: tuple(CommandState, None or Exception)
        """

        if control_char is None:
            if hasattr(protocol, "control_chars"):
                control_char = protocol.control_chars
            else:
                self.logger.debug("Protocol %s doesn't have a control "
                                  "character sequence!" % protocol.name)
                return CommandState.Error, NoControlCharacterException(
                    "Protocol %s doesn't have a control character sequence." %
                    protocol.name
                )

        if our_name is None:
            if hasattr(protocol, "nickname"):
                our_name = protocol.nickname

        if our_name is not None:
            control_char = control_char.replace("{NAME}", our_name)
            control_char = control_char.replace("{NICK}", our_name)

        if len(in_str) < len(control_char):
            self.logger.trace("Control character sequence is longer than the "
                              "input string, so this cannot be a command.")
            return CommandState.NotACommand, None

        if in_str.lower().startswith(control_char.lower()):  # It's a command!
            # Remove the command char(s) from the start
            replaced = in_str[len(control_char):]

            split = replaced.split(None, 1)
            if not split:
                return False
            command = split[0]
            args = ""
            if len(split) > 1:
                args = split[1]

            printable = "<%s:%s> %s" % (caller, source, in_str)

            event = events.PreCommand(protocol, command, args, caller,
                                      source, printable, in_str)
            self.event_manager.run_callback("PreCommand", event)

            if event.printable:
                self.logger.info("%s | %s" % (protocol.name,
                                              event.printable)
                                 )

            result = self.run_command(event.command, event.source,
                                      event.target, protocol, event.args)

            return result

        self.logger.debug("Command not found.")
        return CommandState.NotACommand, None

    def run_command(self, command, caller, source, protocol, args):
        """Run a command, provided it's been registered.

        :param command: The command, a string
        :param caller: Who ran the command
        :param source: Where they ran the command
        :param protocol: The protocol they're part of
        :param args: A list of arguments for the command

        :type command: str
        :type caller: User
        :type source: User
        :type protocol: Protocol
        :type args: list

        :return: Tuple containing CommandState representing the state of
            the command, and either None or an Exception.
        :rtype: tuple(CommandState, None or Exception)
        """

        if command not in self.commands:
            if command not in self.aliases:  # Get alias, if it exists
                event = events.UnknownCommand(self, protocol, command, args,
                                              caller, source)

                self.event_manager.run_callback("UnknownCommand", event)

                if event.cancelled:
                    return CommandState.UnknownOverridden, None

                return CommandState.Unknown, None
            command = self.aliases[command]
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

        # Check command permission if it has one
        cmd_obj = self.commands[command]
        if cmd_obj["permission"]:
            # Use permission handler if there is one
            if self.perm_handler:
                if not self.perm_handler.check(cmd_obj["permission"],
                                               caller, source, protocol):
                    return CommandState.NoPermission, None
            else:
                # No perm handler, check if default-allowed
                if not cmd_obj["default"]:
                    return CommandState.NoPermission, None

        # No permission problems, run the command!
        try:
            cmd_obj["f"](protocol, caller, source, command, raw_args,
                         parsed_args)
        except UsageError as e:
            return CommandState.InvalidUsage, e
        except NoPermissionError as e:
            return CommandState.NoPermission, e
        except RateLimitExceededError:
            return CommandState.RateLimited, None
        except CommandError as e:
            return CommandState.UserVisibleError, e
        except Exception as e:
            self.logger.exception("Error running command")
            return CommandState.Error, e
        else:
            return CommandState.Success, None

    @deprecated("Use set_auth_handler instead")
    def add_auth_handler(self, handler):
        return self.set_auth_handler(handler)

    def set_auth_handler(self, handler):
        """Add an auth handler, provided it hasn't already been added.

        :param handler: The handler to add
        :type handler: object

        :returns: Whether the handler was added or not
        :rtype: Boolean
        """
        if self.auth_handler is None:
            self.auth_handler = handler
            return True

        return False

    def set_permissions_handler(self, handler):
        """Set the permissions handler, provided one hasn't already been set.

        :param handler: The handler to set
        :type handler: plugins.auth.permissions_handler.permissionsHandler

        :returns: Whether the handler was set or not
        :rtype: Boolean
        """
        if self.perm_handler:
            self.logger.warn(_("Two plugins are trying to provide permissions "
                               "handlers. Only the first will be used!"))
            return False
        self.perm_handler = handler
        return True


class NoControlCharacterException(Exception):
    pass
