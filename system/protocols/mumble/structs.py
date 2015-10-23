from collections import namedtuple

__author__ = 'Sean'


Version = namedtuple("Version", ["version", "release", "os", "os_version"])


class Stats(object):
    """
    Mumble user connection stats
    """

    def __init__(self, good=0, late=0, lost=0, resync=0):
        self.good = good
        self.late = late
        self.lost = lost
        self.resync = resync

    def __repr__(self):
        return "%s(good=%s, late=%s, lost=%s, resync=%s)" % (
            self.__class__.__name__,
            self.good,
            self.late,
            self.lost,
            self.resync
        )
