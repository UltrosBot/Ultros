# coding=utf-8
import signal

from django.utils import importlib
from twisted.internet import reactor

from system.commands.manager import CommandManager
from system.decorators.log import deprecated
from system.enums import PluginState, ProtocolState
from system.events.general import PluginsLoadedEvent, ReactorStartedEvent
from system.events.manager import EventManager
from system.logging import logger
from system.logging.logger import getLogger
from system.metrics import Metrics
from system.plugins.manager import PluginManager
from system.singleton import Singleton
from system.storage.config import Config
from system.storage.formats import YAML
from system.storage.manager import StorageManager
from system.translations import Translations
from utils.misc import valid_path

__author__ = "Gareth Coles"
_ = Translations().get()


class FactoryManager(object):
    """
    Manager for keeping track of multiple factories - one per protocol.

    This is so that the bot can connect to multiple services at once, and have
    them communicate with each other.
    """

    __metaclass__ = Singleton

    #: Instance of the storage manager
    storage = StorageManager()

    #: Storage for all of our factories.
    factories = {}

    #: Storage for each factory module, so we can reload them
    factory_modules = {}

    #: Storage for all of the protocol configs.
    configs = {}

    #: The main configuration is stored here.
    main_config = None

    #: Whether the manager is already running or not
    running = False

    #: Configuration for logging stuff
    logging_config = {}

    def __init__(self):
        self.commands = CommandManager()
        self.event_manager = EventManager()
        self.logger = getLogger("Manager")
        self.plugman = PluginManager(self)

        self.metrics = None

    @property
    def all_plugins(self):
        return self.plugman.info_objects

    @property
    def loaded_plugins(self):
        return self.plugman.plugin_objects

    def setup_logging(self, args):
        """
        Set up logging.
        """

        self.logging_config = self.storage.get_file(
            self, "config", YAML, "logging.yml"
        )

        try:
            if not self.logging_config.exists:
                logger.configure(None)

                self.logger.warn(
                    "No logging config found - using defaults"
                )
                return False
        except IOError:
            logger.configure(None)

            self.logger.error(
                "Unable to load logging configuration at config/logging.yml "
                "- using defaults"
            )
            self.logger.error("Please check that this file exists.")
            return False
        except Exception:
            self.logger.exception(
                "Unable to load logging configuration at config/logging.yml "
                "- using defaults"
            )
            return False

        logger.configure(self.logging_config, args)

        return True

    def setup(self):
        signal.signal(signal.SIGINT, self.signal_callback)

        self.main_config = self.storage.get_file(self, "config", YAML,
                                                 "settings.yml")

        self.commands.set_factory_manager(self)

        self.load_config()  # Load the configuration

        try:
            self.metrics = Metrics(self.main_config, self)
        except Exception:
            self.logger.exception(_("Error setting up metrics."))

        self.plugman.scan()
        self.load_plugins()  # Load the configured plugins
        self.load_protocols()  # Load and set up the protocols

        if not len(self.factories):
            self.logger.info(_("It seems like no protocols are loaded. "
                               "Shutting down.."))
            return

    def run(self):
        if not self.running:
            event = ReactorStartedEvent(self)

            reactor.callLater(0, self.event_manager.run_callback,
                              "ReactorStarted", event)

            self.running = True
            reactor.run()
        else:
            raise RuntimeError(_("Manager is already running!"))

    def signal_callback(self, signum, frame):
        try:
            try:
                self.unload()
            except Exception:
                self.logger.exception(_("Error while unloading!"))
                try:
                    reactor.stop()
                except Exception:
                    try:
                        reactor.crash()
                    except Exception:
                        pass
        except Exception:
            exit(0)

    # Load stuff

    def load_config(self):
        """
        Load the main configuration file.

        :return: Whether the config was loaded or not
        :rtype: bool
        """

        try:
            self.logger.info(_("Loading global configuration.."))
            if not self.main_config.exists:
                self.logger.error(_(
                    "Main configuration not found! Please correct this and try"
                    " again."))
                return False
        except IOError:
            self.logger.error(_(
                "Unable to load main configuration at config/settings.yml"))
            self.logger.error(_("Please check that this file exists."))
            return False
        except Exception:
            self.logger.exception(_(
                "Unable to load main configuration at config/settings.yml"))
            return False
        return True

    def load_plugins(self):
        """
        Attempt to load all of the plugins.
        """

        self.logger.info(_("Loading plugins.."))

        self.logger.trace(_("Configured plugins: %s")
                          % ", ".join(self.main_config["plugins"]))

        self.plugman.load_plugins(self.main_config.get("plugins", []))

        event = PluginsLoadedEvent(self, self.plugman.plugin_objects)
        self.event_manager.run_callback("PluginsLoaded", event)

    @deprecated("Use the plugin manager directly")
    def load_plugin(self, name, unload=False):
        """
        Load a single plugin by name.

        This will return one of the system.enums.PluginState values.

        :param name: The plugin to load.
        :type name: str

        :param unload: Whether to unload the plugin, if it's already loaded.
        :type unload: bool
        """

        result = self.plugman.load_plugin(name)

        if result is PluginState.AlreadyLoaded:
            if unload:
                result_two = self.plugman.unload_plugin(name)

                if result_two is not PluginState.Unloaded:
                    return result_two

                result = self.plugman.load_plugin(name)

        return result

    @deprecated("Use the plugin manager directly")
    def collect_plugins(self):
        """
        Collect all possible plugin candidates.
        """

        self.plugman.scan()

    def load_protocols(self):
        """
        Load and set up all of the configured protocols.
        """

        self.logger.info(_("Setting up protocols.."))

        for protocol in self.main_config["protocols"]:
            if protocol.lower().startswith("plugin-"):
                self.logger.error("Invalid protocol name: %s" % protocol)
                self.logger.error(
                    "Protocol names beginning with \"plugin-\" are reserved "
                    "for plugin use."
                )
                continue

            self.logger.info(_("Setting up protocol: %s") % protocol)
            conf_location = "protocols/%s.yml" % protocol
            result = self.load_protocol(protocol, conf_location)

            if result is not ProtocolState.Loaded:
                if result is ProtocolState.AlreadyLoaded:
                    self.logger.warn(_("Protocol is already loaded."))
                elif result is ProtocolState.ConfigNotExists:
                    self.logger.warn(_("Unable to find protocol "
                                       "configuration."))
                elif result is ProtocolState.LoadError:
                    self.logger.warn(_("Error detected while loading "
                                       "protocol."))
                elif result is ProtocolState.SetupError:
                    self.logger.warn(_("Error detected while setting up "
                                       "protocol."))

    def load_protocol(self, name, conf_location):
        """
        Attempt to load a protocol by name. This can return one of the
        following, from system.constants:

        * PROTOCOL_ALREADY_LOADED
        * PROTOCOL_CONFIG_NOT_EXISTS
        * PROTOCOL_LOAD_ERROR
        * PROTOCOL_LOADED
        * PROTOCOL_SETUP_ERROR

        :param name: The name of the protocol
        :type name: str

        :param conf_location: The location of the config file, relative
            to the config/ directory, or a Config object
        :type conf_location: str, Config
        """

        if name in self.factories:
            return ProtocolState.AlreadyLoaded

        config = conf_location
        if not isinstance(conf_location, Config):
            if not valid_path(self.storage.conf_path + conf_location):
                self.logger.error(
                    "Invalid config location: {}{}".format(
                        self.storage.conf_path, conf_location
                    )
                )

                return

            try:
                config = self.storage.get_file(self, "config", YAML,
                                               conf_location)
                if not config.exists:
                    return ProtocolState.ConfigNotExists
            except Exception:
                self.logger.exception(
                    _("Unable to load configuration for the '%s' protocol.")
                    % name)
                return ProtocolState.LoadError
        try:
            protocol_type = config["main"]["protocol-type"]

            if protocol_type in self.factory_modules:
                factory_module = reload(self.factory_modules[protocol_type])
            else:
                factory_module = importlib.import_module(
                    "system.protocols.{}.factory".format(protocol_type)
                )

            self.factory_modules[protocol_type] = factory_module

            self.factories[name] = factory_module.Factory(name, config, self)
            self.factories[name].connect()
            return ProtocolState.Loaded
        except Exception:
            if name in self.factories:
                del self.factories[name]
            self.logger.exception(
                _("Unable to create factory for the '%s' protocol!")
                % name)
            return ProtocolState.SetupError

    # Reload stuff

    @deprecated("Use the plugin manager directly")
    def reload_plugin(self, name):
        """
        Attempt to reload a plugin by name.

        This will return one of the system.enums.PluginState values.

        :param name: The name of the plugin
        :type name: str
        """
        return self.plugman.reload_plugin(name)

    def reload_protocol(self, name):
        factory = self.get_factory(name)

        if name is not None:
            factory.shutdown()
            factory.setup()
            return True

    # Unload stuff

    @deprecated("Use the plugin manager directly")
    def unload_plugin(self, name):
        """
        Attempt to unload a plugin by name.

        This will return one of the system.enums.PluginState values.

        :param name: The name of the plugin
        :type name: str
        """

        return self.plugman.unload_plugin(name)

    def unload_protocol(self, name):  # Removes with a shutdown
        """
        Attempt to unload a protocol by name. This will also shut it down.

        :param name: The name of the protocol
        :type name: str

        :return: Whether the protocol was unloaded
        :rtype: bool
        """

        if name in self.factories:
            proto = self.factories[name]
            try:
                proto.shutdown()
            except Exception:
                self.logger.exception(_("Error shutting down protocol %s")
                                      % name)
            finally:
                try:
                    self.storage.release_file(self, "config",
                                              "protocols/%s.yml" % name)
                    self.storage.release_files(proto)
                    self.storage.release_files(proto.protocol)
                except Exception:
                    self.logger.exception("Error releasing files for protocol "
                                          "%s" % name)
            del self.factories[name]
            return True
        return False

    def unload(self):
        """
        Shut down and unload everything.
        """

        # Shut down!
        for name in self.factories.keys():
            self.logger.info(_("Unloading protocol: %s") % name)
            self.unload_protocol(name)

        self.plugman.unload_plugins()

        if reactor.running:
            try:
                reactor.stop()
            except Exception:
                self.logger.exception("Error stopping reactor")

    # Grab stuff

    def get_protocol(self, name):
        """
        Get the instance of a protocol, by name.

        :param name: The name of the protocol
        :type name: str

        :return: The protocol, or None if it doesn't exist.
        """

        if name in self.factories:
            return self.factories[name].protocol
        return None

    def get_factory(self, name):
        """
        Get the instance of a protocol's factory, by name.

        :param name: The name of the protocol
        :type name: str

        :return: The factory, or None if it doesn't exist.
        """

        if name in self.factories:
            return self.factories[name]
        return None

    @deprecated("Use the plugin manager directly")
    def get_plugin(self, name):
        """
        Get the insatnce of a plugin, by name.
        :param name: The name of the plugin
        :type name: str

        :return: The plugin, or None if it isn't loaded.
        """

        return self.plugman.get_plugin(name)

    def remove_protocol(self, protocol):  # Removes without shutdown
        """
        Remove a protocol without shutting it down. You shouldn't use this.

        :param protocol: The name of the protocol
        :type protocol: str

        :return: Whether the protocol was removed.
        :rtype: bool
        """

        if protocol in self.factories:
            del self.factories[protocol]
            return True
        return False
