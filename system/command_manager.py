# coding=utf-8
import shlex

__author__ = "Gareth Coles"

from system.decorators.ratelimit import RateLimitExceededError
from system.events import general as events
from system.event_manager import EventManager
from system.singleton import Singleton
from utils.log import getLogger

from system.translations import Translations
_ = Translations().get()


class CommandManager(object):
    """
    This is the command manager. It's in charge of tracking commands that
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

    #: Storage for all the registered auth handlers.
    #:
    #: Auth handlers are in charge of asserting whether users are logged in
    #: or not, and identifying who they are logged in as.
    auth_handlers = []

    #: Storage for the permissions handler. There may only ever be one of
    #: these.
    #:
    #: Permissions handlers are in charge of asserting whether a user has
    #: permission for a specified action. They work together with auth
    #: handlers to determine this.
    perm_handler = None

    #: Storage for the factory manager, to avoid function call overhead.
    factory_manager = None

    def __init__(self):
        self.logger = getLogger("Commands")
        self.event_manager = EventManager()

    def set_factory_manager(self, factory_manager):
        """
        Set the factory manager. This should only ever be called by the
        factory manager itself.

        :param factory_manager: The factory manager
        :type factory_manager: Manager
        """
        self.factory_manager = factory_manager

    def register_command(self, command, handler, owner, permission=None,
                         aliases=None):
        """
        Register a command, provided it hasn't been registered already.
        The params should go like this..

        :param command: The command to register
        :param handler: The command handler
        :param owner: The plugin or object registering the command
        :param permission: The permission needed to run the command
        :param aliases: A list of aliases for the command being registered.

        :type command: str
        :type handler: function
        :type owner: PluginObject
        :type permission: str, None
        :type aliases: list, None

        :returns: Whether the command was registered or not
        :rtype: Boolean
        """

        if aliases is None:
            aliases = []

        if command in self.commands:
            self.logger.warn(_("Object '%s' tried to register command '%s' but"
                               "it's already been registered by object '%s'.")
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
            "owner": owner
        }

        self.commands[command] = commandobj

        for alias in aliases:
            if alias in self.commands:
                self.logger.warn(_("Failed to register command alias '%s' as "
                                   "it already belongs to another command.")
                                 % alias)
                continue

            self.logger.debug(_("Registering alias: %s -> %s (%s)")
                              % (alias, command, owner))
            self.commands[alias] = commandobj
        return True

    def unregister_commands_for_owner(self, owner):
        """
        Unregister all commands that have been registered by a certain object.

        :param owner: The owner to check for

        :type owner: object
        """
        current = self.commands.items()
        for key, value in current:
            if owner is value["owner"]:
                del self.commands[key]
                self.logger.debug(_("Unregistered command: %s") % key)

    def process_input(self, in_str, caller, source, protocol,
                      control_char=None, our_name=None, success=True,
                      failure=False):

        if control_char is None:
            if hasattr(protocol, "control_chars"):
                control_char = protocol.control_chars
            else:
                self.logger.debug("Protocol %s doesn't have a control "
                                  "character sequence!" % protocol.name)
                return failure

        if our_name is None:
            if hasattr(protocol, "nickname"):
                our_name = protocol.nickname

        if our_name is not None:
            control_char = control_char.replace("{NAME}", our_name)
            control_char = control_char.replace("{NICK}", our_name)

        if len(in_str) < len(control_char):
            self.logger.trace("Control character sequence is longer than the "
                              "input string, so this cannot be a command.")
            return failure

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

            if command not in self.commands:
                return failure

            printable = "<%s:%s> %s" % (caller, source, in_str)

            event = events.PreCommand(protocol, command, args, caller,
                                      source, printable, in_str)
            self.event_manager.run_callback("PreCommand", event)

            if event.printable:
                if hasattr(protocol, "log"):
                    protocol.log.info(event.printable)
                elif hasattr(protocol, "logger"):
                    protocol.logger.info(event.printable)
                else:
                    self.logger.info("%s | %s" % (protocol.name,
                                                  event.printable))

            result = self.run_command(event.command, event.source,
                                      event.target, protocol, event.args)

            if result[0]:
                self.logger.trace("Command ran successfully.")
                return success

            if result[1] is True:
                self.logger.debug("User doesn't have permission for this "
                                  "command.")
                return success

            if result[1] is None:
                self.logger.debug("Command not found.")
                return failure

            self.logger.debug("An error occured.")
            return success

        self.logger.debug("Command not found.")
        return failure

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
        if command not in self.commands:
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

                    if self.perm_handler.check(self.commands
                                               [command]["permission"],
                                               caller, source, protocol):
                        try:
                            self.commands[command]["f"](protocol, caller,
                                                        source, command,
                                                        raw_args,
                                                        parsed_args)
                        except RateLimitExceededError:
                            caller.respond("Rate limit for '%s' exceeded - "
                                           "try again later." % command)
                            return False, True
                        except Exception as e:
                            self.logger.exception("")
                            return False, e
                    else:
                        return False, True
            else:
                self.commands[command]["f"](protocol, caller, source, command,
                                            raw_args, parsed_args)
        except RateLimitExceededError:
            caller.respond("Rate limit for '%s' exceeded - try again later."
                           % command)
            return False, True
        except Exception as e:
            self.logger.exception("")
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
                self.logger.warn(_("Auth handler %s is already registered.")
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
            self.logger.warn(_("Two plugins are trying to provide permissions "
                               "handlers. Only the first will be used!"))
            return False
        self.perm_handler = handler
        return True
