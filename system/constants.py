__author__ = 'Gareth Coles'

#: The current version. This gets replaced if you're using git.
__version__ = "1.0.0"

try:
    from git import repo
    r = repo.Repo(".")
    heads = r.heads
    master = heads[0]
    commit = master.commit

    __version__ = "Git: %s" % commit.id
except:
    pass

# Constants related to (un)loading plugins

#: This means there was an error loading the plugin.
PLUGIN_LOAD_ERROR = -1

#: This means the plugin doesn't exist.
PLUGIN_NOT_EXISTS = 0

#: This means the plugin was loaded successfully.
PLUGIN_LOADED = 1

#: This means the plugin was already loaded.
PLUGIN_ALREADY_LOADED = 2

#: This means the plugin was unloaded successfully.
PLUGIN_UNLOADED = 3

#: This means the plugin is missing another plugin it depends on.
PLUGIN_DEPENDENCY_MISSING = 4

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
