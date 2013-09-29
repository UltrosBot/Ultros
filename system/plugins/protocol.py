# coding=utf-8
__author__ = "Gareth Coles"

import logging
from yapsy.IPlugin import IPlugin


class ProtocolPlugin(IPlugin):
    """
    Super class for creating protocol plugins.

    Protocol plugins are plugins that interact with a specific protocol. As
    such, you may want to use this to do things specific to a protocol, for
    example, handling an RPL_BANLIST for the IRC protocol. This plugin will
    therefore only accept events from the specified protocol, as well as any
    events that are not specific to a protocol. However, it won't accept any
    events from the factories or factory manager.

    You specify the protocol you want to work with by simply placing the plugin
    in the relevant folder. If you need to work with multiple protocols, we
    suggest creating some custom events that a global plugin may listen for
    these events, or creating some custom events that are not protocol
    specific.

    You should also specify the protocol you're targetting by setting a string
    for the `types` variable. You can leave this blank if you want to work
    with all protocols, or specify a list of protocols if you want to work
    with a certain few. This will be checked on plugin load. Specifying the
    empty string will also disable the check. An empty list works too.

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
    protocol = None
    types = ""

    def __init__(self):
        super(ProtocolPlugin, self).__init__()

    def add_variables(self, info, protocol):
        """
        Do not override this function!
        This function is used to store essential data, required for it to
        work properly. It also sets up logging.

        If you override this and don't call super, your plugin WILL NOT WORK.

        :param info:     PluginInfo Contains plugin info
        :param protocol: Protocol   Used to interact with the server/clients
        """

        self.info = info
        self.module = self.info.path.replace("\\", "/").split("/")[-1]
        self.logger = logging.getLogger(self.module.title())
        self.protocol = protocol

    def activate(self):
        """
        Called when the plugin is loaded.
        Not to be used for setup! You probably don't need this at all.
        """
        super(ProtocolPlugin, self).activate()

    def deactivate(self):
        """
        Called when the plugin is unloaded.
        Use this for saving data or cleaning up.
        """
        super(ProtocolPlugin, self).deactivate()

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
