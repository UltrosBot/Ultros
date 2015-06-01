# coding=utf-8
__author__ = "Gareth Coles"


from system.command_manager import CommandManager
from system.event_manager import EventManager
from system.translations import Translations
from system.storage.manager import StorageManager
_ = Translations().get()


class PluginObject(object):
    """
    Super class for creating plugins.

    Inherit this class when you create your plugin. Don't forget to call
    super() on all methods you override!

    Remember to be careful when naming your plugin. Be descriptive, but
    concise!
    """

    #: :type: CommandManager
    commands = None  # Command manager singleton

    #: :type: EventManager
    events = None  # Event manager singleton

    #: :type: FactoryManager
    factory_manager = None  # Instance of the factory manager

    info = None  # Plugin info object
    logger = None  # Standard python Logger named appropriately
    module = ""  # Module the plugin exists in

    #: :type: system.plugins.manager.PluginManager
    plugins = None  # Plugin manager singleton

    #: :type: StorageManager
    storage = None  # Storage manager

    def add_variables(self, info, factory_manager):
        """
        Adds essential variables at load time and sets up logging

        Do not override this function! If you *do* override this and don't call
        super, your plugin WILL NOT WORK.

        :param info: The plugin info file
        :type info: Info instance

        :param factory_manager: The factory manager
        :type factory_manager: Manager instance
        """

        from system.plugins.manager import PluginManager

        self.commands = CommandManager()
        self.events = EventManager()
        self.factory_manager = factory_manager
        self.info = info
        self.module = self.info.module
        self.plugins = PluginManager()
        self.storage = StorageManager()

    def deactivate(self):
        """
        Called when the plugin is unloaded

        This is intended to be used for last-minute saving and cleanup.
        """

        pass

    def reload(self):
        """
        Note: **Not currently used**

        Called when the plugin should reload its configuration.

        It should return True if the reload succeeded, and False if not.
        If you return None, then it will be treated as if it doesn't exist.
        """

        return None

    def setup(self):
        """
        Called when the plugin is loaded

        This is used for setting up the plugin.
        Remember to override this function!

        Remember, **self.info**, **self.events**, **self.commands**,
        **self.plugins** and **self.factory** are available here, but not in
        **__init__**.
        """

        self.logger.warn(_("Setup method not defined!"))

    def _disable_self(self):
        """
        Convenience method for disabling the current plugin.
        """

        self.factory_manager.plugman.unload_plugin(self.info.name)
