# coding=utf-8

"""
Subclass of Logbook's ColorizedStderrHandler that provides better colours.
"""

__author__ = 'Gareth Coles'

from logbook.base import CRITICAL, ERROR, WARNING, NOTICE, INFO, DEBUG, TRACE
from logbook.more import ColorizedStderrHandler


class ColourHandler(ColorizedStderrHandler):

    def get_colour(self, record):
        """
        Returns the colour for this record.
        """
        if record.level == CRITICAL:
            return "darkred"
        elif record.level == ERROR:
            return "red"
        elif record.level == WARNING:
            return "yellow"
        elif record.level == NOTICE:
            return "green"
        elif record.level == INFO:
            return "lightgray"  # White?
        elif record.level == DEBUG:
            return "blue"
        elif record.level == TRACE:
            return "fuchsia"  # Magenta?
        else:
            return "lightgray"  # White?

    get_color = get_colour
