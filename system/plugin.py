# coding=utf-8
__author__ = "Gareth Coles"

from yapsy.IPlugin import IPlugin


class PluginObject(IPlugin):
    """
    Super class for creating plugins.

    Inherit this class when you create your plugin. Don't forget to call
    super() on all methods you override!

    Remember to be careful when naming your plugin. Be descriptive, but
    concise!
    """

    #: Storage for the PluginInfo object
    info = None

    #: Name of the plugin module, populated automatically
    module = ""

    #: Assigned instance of the standard Python logger
    logger = None

    #: Stored instance of the factory manager, for convenience
    factory_manager = None

    def __init__(self):
        super(PluginObject, self).__init__()

    def add_variables(self, info, factory_manager):
        """
        Do not override this function!
        This function is used to store essential data, required for it to
        work properly. It also sets up logging.

        If you override this and don't call super, your plugin WILL NOT WORK.

        :param info: The plugin info file
        :type info: PluginInfo instance

        :param factory_manager: The factory manager
        :type factory_manager: Manager instance
        """

        self.info = info
        self.module = self.info.path.replace("\\", "/").split("/")[-1]
        self.factory_manager = factory_manager

    def activate(self):
        """
        Called when the plugin is loaded.

        Not to be used for setup! You probably don't need this at all. It's
        a Yapsy convention, but critical objects aren't available in this
        function call.
        """
        super(PluginObject, self).activate()

    def deactivate(self):
        """
        Called when the plugin is unloaded.

        This is intended to be used for last-minute saving and cleanup.
        """
        super(PluginObject, self).deactivate()

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
        Called when the plugin is loaded.
        This is used for setting up the plugin.
        Remember to override this function!

        Remember, **self.info** and **self.factory** are only available once
        this method is called.
        """
        self.logger.warn("Setup method not defined!")

    def _disable_self(self):
        self.factory_manager.plugman.deactivatePluginByName(self.info.name)
