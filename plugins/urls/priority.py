from enum import Enum

__author__ = 'Gareth Coles'


class Priority(object):
    MONITOR = -100  # Only really for the website handler
    LATEST = 0
    LATER = 20
    LATE = 40
    EARLY = 60
    EARLIER = 80
    EARLIEST = 100
