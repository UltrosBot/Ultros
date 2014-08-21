"""Various monitors for Python stuff"""

__author__ = 'Gareth Coles'

import gc
from twisted.internet import reactor

from system.translations import Translations
_ = Translations().get()


class UncollectableMonitor(object):
    """Monitor for objects Python's GC can't collect"""

    def __init__(self, logger, period=120):
        known = {}
        self.logger = logger

        # set this if you want python to print out when uncollectable
        # objects are detected; will print out all objects in the cycle,
        # not just the one(s) that caused the cycle to be uncollectable

        gc.set_debug(
            gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_INSTANCES | gc.DEBUG_OBJECTS
        )

        def sample():
            self.logger.trace(_("Running collection.."))
            gc.collect()
            for o in gc.garbage:
                if o not in known:
                    known[o] = True
                    self.uncollectable(o)
            reactor.callLater(period, sample)

        self.logger.info(_("Starting uncollectable objects monitor."))
        reactor.callLater(0, sample)

    def uncollectable(self, obj):
        self.logger.warn(_("Uncollectable object cycle in gc.garbage!"))

        self.logger.warn(_("Parents:"))
        self._printParents(obj, 2)

        self.logger.warn(_("Children:"))
        self._printKids(obj, 2)

    def _printParents(self, obj, level, indent=' '):
        self.logger.warn("%s%s" % (indent, self._shortRepr(obj)))
        if level > 0:
            for p in gc.get_referrers(obj):
                self._printParents(p, level - 1, indent + " ")

    def _printKids(self, obj, level, indent=' '):
        self.logger.warn("%s%s" % (indent, self._shortRepr(obj)))
        if level > 0:
            for kid in gc.get_referents(obj):
                self._printKids(kid, level - 1, indent + " ")

    def _shortRepr(self, obj):
        if not isinstance(obj, dict):
            return '%s %r @ 0x%x' % (type(obj).__name__, obj, id(obj))
        else:
            keys = obj.keys()
            keys.sort()
            return _("dict with keys %r @ 0x%x") % (keys, id(obj))
