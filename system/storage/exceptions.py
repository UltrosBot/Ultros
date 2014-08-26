"""
Exceptions related to storage of data and configuration files.
"""

__author__ = 'Gareth Coles'


class NotReadyError(Exception):
    """Thrown when the file isn't yet ready for use"""
    pass


class AlreadyRegisteredError(Exception):
    """Thrown when the file is already registered somewhere"""
    pass


class UnknownStorageTypeError(Exception):
    """Thrown when an unknown storage format is given"""
    pass
