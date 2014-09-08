__author__ = 'Gareth Coles'

#: The current version. This gets replaced if you're using git.
__version__ = "1.1.0"
__version_info__ = "Not being run from a Git repo."
__release__ = "1.1.0"

import datetime
from system import enums

try:
    from git import repo
    r = repo.Repo(".")
    heads = r.heads
    master = heads[0]
    commit = master.commit

    __version__ = "Git: %s" % commit
    __version_info__ = "Last commit by %s (%s) - %s" % \
                       (commit.author,
                        datetime.datetime.fromtimestamp(
                            commit.committed_date
                        ).strftime("%d %b, %Y - %H:%M:%S"),
                        commit.summary.replace("\n", " / "))
except Exception as e:
    if __version__ is None:
        __version__ = "1.0.0"
        __version_info__ = "Unable to get last commit."

# Constants related to (un)loading plugins

#: This means there was an error loading the plugin.
PLUGIN_LOAD_ERROR = enums.PluginState.LoadError

#: This means the plugin doesn't exist.
PLUGIN_NOT_EXISTS = enums.PluginState.NotExists

#: This means the plugin was loaded successfully.
PLUGIN_LOADED = enums.PluginState.Loaded

#: This means the plugin was already loaded.
PLUGIN_ALREADY_LOADED = enums.PluginState.AlreadyLoaded

#: This means the plugin was unloaded successfully.
PLUGIN_UNLOADED = enums.PluginState.Unloaded

#: This means the plugin is missing another plugin it depends on.
PLUGIN_DEPENDENCY_MISSING = enums.PluginState.DependencyMissing

# Constants related to (un)loading protocols

#: This means there was a problem setting up the protocol.
PROTOCOL_SETUP_ERROR = -3

#: This means there was a problem loading the protocol and its config.
PROTOCOL_LOAD_ERROR = -2

#: This means that the configuration file for the protocol doesn't exit.
PROTOCOL_CONFIG_NOT_EXISTS = -1

#: This means that the protocol doesn't exit.
PROTOCOL_NOT_EXISTS = 0

#: This means that the protocol was loaded successfully.
PROTOCOL_LOADED = 1

#: This means that the protocol was already loaded.
PROTOCOL_ALREADY_LOADED = 2

#: This means that the protocol was unloaded successfully.
PROTOCOL_UNLOADED = 3
