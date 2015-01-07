__author__ = 'Gareth Coles'

# So we can translate logging levels
import logging

# Logbook stores its levels and their info here
import logbook.base

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
reverse_level_names = {v: k for k, v in level_names.iteritems()}

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


from logbook import Logger


# This is our own Logger, which also has a .trace()
class OurLogger(Logger):

    def trace(self, *args, **kwargs):
        """
        Same as Logbook's debug, etc functions, but for a custom TRACE level.
        """

        if not self.disabled and logbook.TRACE >= self.level:
            self._log(logbook.TRACE, args, kwargs)

    def setLevel(self, level):
        """
        Takes a level from the standard python logging module
        and translates it so this logger can use it.
        """

        if level == logging.CRITICAL:
            self.level_name = logbook.base.CRITICAL
        elif level == logging.ERROR:
            self.level_name = logbook.base.ERROR
        elif level == logging.WARNING:
            self.level_name = logbook.base.WARNING
        elif level == logging.ERROR:
            self.level_name = logbook.base.ERROR
        elif level == logging.INFO:
            self.level_name = logbook.base.INFO
        elif level == logging.DEBUG:
            self.level_name = logbook.base.DEBUG
        elif level == logging.NOTSET:
            self.level_name = logbook.base.NOTSET
        else:
            self.level_name = level
