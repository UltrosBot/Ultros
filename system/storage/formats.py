# coding=utf-8

"""
Storage file format definitions
"""

__author__ = 'Gareth Coles'

from enum import Enum


class Formats(Enum):
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
