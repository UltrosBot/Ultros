__author__ = 'Gareth Coles'

from enum import Enum

"""
Enums for various different things.

These will mostly be used to confer some kind of state.
"""


class HelpTopicType(Enum):
    """The various types a help topic can be.

    These types will define what a help topic may contain.

    * GenericTopic - Doesn't contain any special data
    * CommandTopic - Contains information specific to a command
    """

    GenericTopic = 0
    CommandTopic = 1


class CommandState(Enum):
    """The state of a command that's been run.

    * RateLimited - The command has been rate-limited.
    * NotACommand - The input string wasn't actually a command.
    * UnknownOverridden - The command was unknown but something cancelled the
        UnknownCommand event.
    * Unknown - The command was unknown.
    * Success - The command was run without problems.
    * NoPermission - The command wasn't run due to a lack of permissions.
    * Error - There was an error while running the command.

    Remember, this is an enum - don't try to use the values directly or
    instantiate the class!
    """

    RateLimited = -4
    NotACommand = -3
    UnknownOverridden = -2
    Unknown = -1
    Success = 0
    NoPermission = 1
    Error = 2


class PluginState(Enum):
    LoadError = -1
    NotExists = 0
    Loaded = 1
    AlreadyLoaded = 2
    Unloaded = 3
    DependencyMissing = 4


class ProtocolState(Enum):
    SetupError = -3
    LoadError = -2
    ConfigNotExists = -1
    NotExists = 0
    Loaded = 1
    AlreadyLoaded = 2
    Unloaded = 3
