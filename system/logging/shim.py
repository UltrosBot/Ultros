"""
Semi-hacky stuff to make Logbook suitable for use with Ultros.

Your all-access-pass to Logbookdom includes:

* A trace logging level, which includes shifting the other levels up to make
    room for it
    * A small amount of duck-punching so TRACE can be imported from the logbook
      packages
* A custom logger that includes a .trace() method and simple handlers list, as
  well as a .setLevel() that works with Python's standard logging levels and a
  .failure(message, Failure) for logging Twisted Failures
* A logger forwarder so that loggers can be recreated without modules having
  to grab the new instances
"""

import logging
import logbook.base

from logbook import Logger

from kitchen.text.converters import to_bytes
from twisted.python.failure import Failure

__author__ = 'Gareth Coles'

# Bump up all the logging levels and add our own at the bottom
our_CRITICAL = logbook.base.CRITICAL + 1
our_ERROR = logbook.base.ERROR + 1
our_WARNING = logbook.base.WARNING + 1
our_NOTICE = logbook.base.NOTICE + 1
our_INFO = logbook.base.INFO + 1
our_DEBUG = logbook.base.DEBUG + 1
our_TRACE = logbook.base.DEBUG
our_NOTSET = logbook.base.NOTSET

# Create the dict of level names
level_names = {
    our_CRITICAL: "CRITICAL",
    our_ERROR: "ERROR",
    our_WARNING: "WARNING",
    our_NOTICE: "NOTICE",
    our_INFO: "INFO",
    our_DEBUG: "DEBUG",
    our_TRACE: "TRACE",
    our_NOTSET: "NOTSET"
}

# Swap the keys and values for reverse lookup
reverse_level_names = {}

for k, v in level_names.iteritems():
    reverse_level_names[v] = k

# Set the logging levels on the logbook base
setattr(logbook.base, "CRITICAL", our_CRITICAL)
setattr(logbook.base, "ERROR", our_ERROR)
setattr(logbook.base, "WARNING", our_WARNING)
setattr(logbook.base, "NOTICE", our_NOTICE)
setattr(logbook.base, "INFO", our_INFO)
setattr(logbook.base, "DEBUG", our_DEBUG)
setattr(logbook.base, "TRACE", our_TRACE)
setattr(logbook.base, "NOTSET", our_NOTSET)

# Set them on the main logbook module
setattr(logbook, "CRITICAL", our_CRITICAL)
setattr(logbook, "ERROR", our_ERROR)
setattr(logbook, "WARNING", our_WARNING)
setattr(logbook, "NOTICE", our_NOTICE)
setattr(logbook, "INFO", our_INFO)
setattr(logbook, "DEBUG", our_DEBUG)
setattr(logbook, "NOTSET", our_NOTSET)
setattr(logbook, "TRACE", our_TRACE)

# Set the level names on the logbook base
setattr(logbook.base, "_level_names", level_names)
setattr(logbook.base, "_reverse_level_names", reverse_level_names)


# This is our own Logger, which also has a .trace()
class OurLogger(Logger):
    handlers = []

    def _log(self, level, args, kwargs):
        args = list(args)
        args[0] = to_bytes(args[0])

        super(OurLogger, self)._log(level, args, kwargs)

    def trace(self, *args, **kwargs):
        """
        Same as Logbook's debug, etc functions, but for a custom TRACE level.
        """

        if not self.disabled and logbook.TRACE >= self.level:
            self._log(logbook.TRACE, args, kwargs)

    def failure(self, message, failure, *args, **kwargs):
        """
        Used for logging Twisted Failures via the standard exception() handler,
        which submits errors to metrics
        """

        e = failure.value
        f = failure

        while isinstance(e, Failure):
            try:
                f = e
                e = f.value
            except Exception:
                # If we have a broken Failure instance with no value
                f = failure
                break

        kwargs["exc_info"] = (
            f.type, e, f.tb
        )

        self.exception(message, *args, **kwargs)

    def setLevel(self, level):
        """
        Takes a level from the standard python logging module or a string name
        and translates it so this logger can use it.
        """

        if isinstance(level, basestring):
            self.level_name = reverse_level_names.get(level)

        if level == logging.CRITICAL:
            self.level_name = our_CRITICAL
        elif level == logging.ERROR:
            self.level_name = our_ERROR
        elif level == logging.WARNING:
            self.level_name = our_WARNING
        elif level == logging.INFO:
            self.level_name = our_INFO
        elif level == logging.DEBUG:
            self.level_name = our_DEBUG
        elif level == logging.NOTSET:
            self.level_name = our_NOTSET
        else:
            self.level_name = level


class LoggerForwarder(object):
    """
    Forwarding class that lets us reassign a logger instance when handlers
    need to be reapplied.

    This means that other parts of Ultros that want to do logging don't need to
    constantly call getLogger() - they can just save their logger objects.
    """

    logger = None
    name = ""

    def __init__(self, logger, name):
        self.logger = logger
        self.name = name

    def reassign(self, logger):
        self.logger = logger

    def __getattr__(self, item):
        logger = self.__getattribute__("logger")

        if hasattr(logger, item):
            return getattr(logger, item)
        return self.__getattribute__(item)
