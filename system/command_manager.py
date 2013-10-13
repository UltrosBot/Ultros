# coding=utf-8
__author__ = "Gareth Coles"
from utils.log import getLogger


class CommandManager(object):
    """
    This is the command manager. It's in charge of tracking commands that
    plugins wish to offer, and providing ways for plugins to offer methods
    of providing authentication and permissions.
    """

    commands = {}
    auth_handlers = []
    perm_handler = None

    # commands = {
    #   "command": {
    #     "f": func(),
    #     "permission": "plugin.command",
    #     "owner": <instance of system.plugin.Plugin>
    #   }
    # }

    def __init__(self, factory_manager):
        self.factory_manager = factory_manager
        self.logger = getLogger("Commands")

    def register_command(self, command, handler, owner, permission=None):
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
            "owner": owner
        }
        return True

    def run_command(self, command, caller, source, protocol, args):
        if not command in self.commands:
            return False, None
        try:
            if self.commands[command]["permission"]:
                if not self.perm_handler or not self.auth_handlers:
                    return False, None
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
                            self.commands[command]["f"](caller, source,
                                                        args, protocol)
                    else:
                        return False, True
            else:
                self.commands[command]["f"](caller, source, args, protocol)
        except Exception as e:
            return False, e
        else:
            return True, None

    def set_auth_handler(self, handler):
        for instance in self.auth_handlers:
            if isinstance(instance, handler):
                self.logger.warn("Auth handler %s is already registered."
                                 % handler)
                return False

        self.auth_handlers.append(handler())
        return True

    def set_permissions_handler(self, handler):
        if self.perm_handler:
            self.logger.warn("Two plugins are trying to provide permissions "
                             "handlers. Only the first will be used!")
            return False
        self.auth_handlers.append(handler())
        return True
