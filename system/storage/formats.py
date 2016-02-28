# coding=utf-8
from enum import Enum

"""
Storage file format definitions.
"""

__author__ = 'Gareth Coles'


class Formats(Enum):
    """
    An enum containing each supported file format

    [C ] means that the format is supported for config files.
    [ D] means that the format is supported for data files.
    [CD] means that the format is supported for both.

    * [*CD*] **Formats.YAML** - YaML
    * [*CD*] **Formats.JSON** - JSON
    * [*CD*] **Formats.MEMORY** - In-memory dictionary
    * [* D*] **Formats.DBAPI** - Twisted ADBAPI database
    * [* D*] **Formats.MONGO** - MongoDB
    * [* D*] **Formats.REDIS** - Redis
    """

    YAML = "Yaml"
    JSON = "JSON"
    MEMORY = "Memory"
    DBAPI = "DBAPI"
    MONGO = "MongoDB"
    REDIS = "Redis"

# TODO: Remove enum references below

YAML = Formats.YAML
JSON = Formats.JSON
MEMORY = Formats.MEMORY
DBAPI = Formats.DBAPI
MONGO = Formats.MONGO
REDIS = Formats.REDIS

DATA = [YAML, JSON, MEMORY, DBAPI, MONGO, REDIS]
CONF = [YAML, JSON, MEMORY]
ALL = [YAML, JSON, MEMORY]
