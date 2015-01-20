"""
Some handlers need factory functions to translate configurations. Essentially,
this allows saner user-provided configurations.

These are intended to be supplied instead of classes when adding handlers for
loggers.
"""

__author__ = 'Gareth Coles'

import os

from logbook import NTEventLogHandler, SyslogHandler


def create_syshandler(*_, **__):
    """
    Get yourself the correct system log handler.

    You shouldn't need to use this directly.

    :param _: Unused, ignored
    :param __: Unused, ignored
    :return: Logbook logger for logging to this OS's system logs
    """

    if os.name == 'nt':
        return NTEventLogHandler("Ultros")
    return SyslogHandler("Ultros")
