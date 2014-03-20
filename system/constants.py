__author__ = 'Gareth Coles'
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

PLUGIN_LOAD_ERROR = -1
PLUGIN_NOT_EXISTS = 0
PLUGIN_LOADED = 1
PLUGIN_ALREADY_LOADED = 2
PLUGIN_UNLOADED = 3
PLUGIN_DEPENDENCY_MISSING = 4

# Constants related to (un)loading protocols

PROTOCOL_SETUP_ERROR = -3
PROTOCOL_LOAD_ERROR = -2
PROTOCOL_CONFIG_NOT_EXISTS = -1
PROTOCOL_NOT_EXISTS = 0
PROTOCOL_LOADED = 1
PROTOCOL_ALREADY_LOADED = 2
PROTOCOL_UNLOADED = 3
