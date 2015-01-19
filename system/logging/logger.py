__author__ = 'Gareth Coles'

"""
Logbook-based logging, modified a bit to suit our purposes.

Logbook turned out to be fairly complicated. Who knew? Still, it adds a lot
of things to the logging system that would have been a huge pain to do
ourselves, and our new logging system allows plugins to modify various aspects
of logging, as well as provide additional handlers.
"""

import os

import system.logging.shim as shim

from logbook import INFO, NOTSET, NullHandler, NTEventLogHandler, SyslogHandler
from system.logging.handlers.colours import ColourHandler


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


#: Default handler list
defaults = [
    "boxcar", "email", "redis", "system", "colour",
    "growl", "libnotify", "twitter", "external", "null"
]

#: Storage for the configuration of each handler
configuration = {
    "format_string": "{record.time:%b %d %Y - %H:%M:%S} | "
                     "{record.channel:<25} | {record.level_name:<8} | "
                     "{record.message}",
    "handlers": {
        "boxcar": False,
        "email": False,
        "external": False,
        "growl": False,
        "libnotify": False,
        "redis": False,
        "system": False,
        "twitter": False,

        # Constants
        "colour": True,
        "null": [NOTSET]
    },

    "configured": False,
    "level": INFO
}

#: Cached loggers
loggers = {}

#: Each handler object
handlers = {
    # Default handlers

    # "boxcar": False,
    # "email": False,
    # "external": False,
    # "growl": False,
    # "libnotify": False,
    # "redis": False,
    # "system": False,
    # "twitter": False,

    "colour": ColourHandler,
    "null": NullHandler,
    "system": create_syshandler
}

# The order handlers should be added to loggers
handler_order = [
    "boxcar", "email", "redis", "colour", "growl",
    "libnotify", "twitter", "external", "system", "null"
]


def getLogger(name, add_handlers=True):
    """
    Get yourself a logger for normal use.

    This will be the function you want to use for logging, most of the time.
    You don't have to store the logger, but it's probably more efficient if
    you do, despite our caching.

    :param name: The name of your logger
    :param add_handlers: Whether to add all the configured handlers, or skip it

    :type name: basestring
    :type add_handlers: bool

    :return: A wrapped logger, suitable for use anywhere
    """

    if name in loggers:
        return loggers[name]
    else:
        actual_logger = shim.OurLogger(name)
        logger = shim.LoggerForwarder(actual_logger, name)

        if add_handlers:
            add_all_handlers(logger)

        loggers[name] = logger
        return loggers[name]


def add_all_handlers(logger):
    """
    Add all the configured handlers to a logger.

    If you need to use this, you're doing something wrong.

    :type logger: shim.OurLogger, shim.LoggerForwarder
    :param logger: The logger to add the handlers to
    """

    if not configuration["configured"]:
        return

    for handler in handler_order:
        config = configuration["handlers"].get(handler, False)
        if config is None:
            continue

        if isinstance(config, bool) and not config:
            continue

        #: :type: logbook.Handler
        handler_obj = handlers.get(handler, None)

        if handler_obj is None:
            continue

        try:
            if isinstance(config, dict):
                default = {
                    "level": configuration["level"],
                    "format_string": configuration["format_string"],
                    "bubble": True
                }

                default.update(config)

                logger.handlers.append(handler_obj(
                    **default
                ))
            elif isinstance(config, list):
                logger.handlers.append(handler_obj(
                    *config
                ))
            else:
                logger.handlers.append(handler_obj(
                    level=configuration["level"],
                    format_string=configuration["format_string"]
                ))
        except Exception as e:
            print(
                "Unable to add handler {} to logger {}: {}".format(
                    handler, logger.name, e
                )
            )


def redo_handlers(logger):
    """
    Remove all the handlers from a logger and add all the configured handlers
    to it again.

    This is used on every logger every time the handlers list is modified.

    :param logger: The logger to redo
    :type logger: basestring, shim.LoggerForwarder
    """

    if isinstance(logger, shim.LoggerForwarder):
        logger_name = logger.name
    else:
        logger_name = logger

    if logger_name in loggers:
        loggers[logger_name].handlers = []

        add_all_handlers(logger)


def redo_all_handlers():
    """
    Remove all handlers from all loggers and add the configured handlers
    back to them.
    """

    for logger in loggers.itervalues():
        redo_handlers(logger)


def configure(config):
    """
    For internal use, loads the configuration from a dict.

    This is used internally - you shouldn't need this.

    :param config: Dict to load configuration from
    :type config: dict
    """

    if config is not None:
        configuration["format_string"] = config.get(
            "format_string", configuration["format_string"]
        )
        configuration["handlers"] = config.get(
            "handlers", configuration["handlers"]
        )
        configuration["level"] = config.get("level", configuration["level"])

        configuration["handlers"].update({
            # Constants
            "colour": True,
            "null": [NOTSET]
        })

    configuration["configured"] = True

    for logger in loggers.values():
        add_all_handlers(logger)

# Handler ordering


def handler_before(this, before):
    """
    For handler ordering - specify that your handler should be added before
        another.

    :param this: Your handler
    :param before: The handler to put after yours

    :type this: str
    :type before: str
    """

    if this in handler_order:
        return

    if before in handler_order:
        handler_order.insert(handler_order.index(before), this)
    else:
        handler_order.append(this)


def handler_after(this, after):
    """
    For handler ordering - specify that your handler should be added after
        another.

    :param this: Your handler
    :param after: The handler to put before yours

    :type this: str
    :type after: str
    """

    if this in handler_order:
        return

    if after in handler_order:
        handler_order.insert(handler_order.index(after) + 1, this)
    else:
        handler_order.append(this)

# Handler registration


def add_handler(name, handler):
    """
    Register your handler proper. This will recreate all handlers on all
    loggers, so you should only do this when your plugin is loaded, for
    instance.

    :param name: The name of your handler
    :param handler: The handler class

    :type name: str
    :type handler: object
    """

    if name in handlers:
        return

    handlers[name] = handler

    redo_all_handlers()


def remove_handler(name):
    """
    Remove a registered handler. This will recreate all handlers on all
    loggers, so you should use this very sparingly, in special circumstances
    only.

    :param name: The name of the handler to remove
    :type name: str
    """

    if name in handlers:
        del handlers[name]

        redo_all_handlers()
