__author__ = 'Gareth Coles'

"""

"""

import os

import system.logging.shim as shim

from logbook import INFO, NOTSET, NullHandler, NTEventLogHandler, SyslogHandler
from system.logging.handlers.colours import ColourHandler

# ["Ultros", "Application", ERROR, None, None, True]


def create_syshandler(*_, **__):
    if os.name == 'nt':
        return NTEventLogHandler("Ultros")
    return SyslogHandler("Ultros")


defaults = [
    "boxcar", "email", "redis", "system", "colour",
    "growl", "libnotify", "twitter", "external", "null"
]

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

loggers = {}

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

handler_order = [
    "boxcar", "email", "redis", "colour", "growl",
    "libnotify", "twitter", "external", "system", "null"
]


def getLogger(name, add_handlers=True):
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
    :type logger: shim.OurLogger, shim.LoggerForwarder
    :param logger:
    :return:
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
                    "format_string": configuration["format_string"]
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
    if isinstance(logger, shim.LoggerForwarder):
        logger_name = logger.name
    else:
        logger_name = logger

    if logger_name in loggers:
        loggers[logger_name].handlers = []

        add_all_handlers(logger)


def redo_all_handlers():
    for logger in loggers.itervalues():
        redo_handlers(logger)


def configure(config):
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
    if this in handler_order:
        return

    if before in handler_order:
        handler_order.insert(handler_order.index(before), this)
    else:
        handler_order.append(this)


def handler_after(this, after):
    if this in handler_order:
        return

    if after in handler_order:
        handler_order.insert(handler_order.index(after) + 1, this)
    else:
        handler_order.append(this)

# Handler registration


def add_handler(name, handler):
    if name in handlers:
        return

    handlers[name] = handler

    redo_all_handlers()
