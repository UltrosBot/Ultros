# coding=utf-8
__author__ = "Gareth Coles"

import logging
from yapsy.IPlugin import IPlugin


class GlobalPlugin(IPlugin):
    """
    Super class for creating global plugins.

    Global plugins are plugins that interact with the factory manager and
    accept all events. They can provide functionality to any of the protocols,
    but protocol plugins are a much better idea if you want to support certain
    events from them, such as the RPL_BANLIST from IRC protocols.GlobalPlugin

    Inherit this class when you create your global plugin. You can override
    the following methods, but remember to call super() on them!
    - activate (self): Called on plugin load
     - It's best not to use this one. It gets called before the plugin info
       and FactoryManager are available.
    - deactivate(self): Called on plugin deactivation
     - You can clean up and save data here.
    - setup(self):
     - Do your plugin setup here. This can include setting up events and other
       things. The plugin info and FactoryManager are available here.

    Remember to be careful when naming your plugin. Be descriptive, but
    concise!
    """

    info = None
    module = ""
    logger = None
    factory_manager = None

    def __init__(self):
        super(GlobalPlugin, self).__init__()

    def add_variables(self, info, factory_manager):
        """
        Do not override this function!
        This function is used to store essential data, required for it to
        work properly. It also sets up logging.

        If you override this and don't call super, your plugin WILL NOT WORK.

        :param info:            PluginInfo      Contains plugin info
        :param factory_manager: FactoryManager  Used to interact with the core
        """

        self.info = info
        self.module = self.info.path.replace("\\", "/").split("/")[-1]
        self.logger = logging.getLogger(self.module.title())
        self.factory_manager = factory_manager

    def activate(self):
        """
        Called when the plugin is loaded.
        Not to be used for setup! You probably don't need this at all.
        """
        super(GlobalPlugin, self).activate()

    def deactivate(self):
        """
        Called when the plugin is unloaded.
        Use this for saving data or cleaning up.
        """
        super(GlobalPlugin, self).deactivate()

    def setup(self):
        """
        Called when the plugin is loaded.
        This is used for setting up the plugin.
        Remember to override this function!

        Don't use activate for this.
        self.info and self.factory are only available once this method is
        called.
        """
        pass