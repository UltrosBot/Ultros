__author__ = 'Gareth Coles'

"""

"""

from logbook import INFO, NullHandler

import system.logging.shim as shim
from system.logging.handlers.colours import ColourHandler


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
        "twitter": False
    },

    "configured": False
}

loggers = {}


def getLogger(name, add_handlers=True):
    if name in loggers:
        return loggers[name]
    else:
        logger = shim.OurLogger(name)

        if add_handlers:
            add_standard_handlers(logger)

        loggers[name] = logger
        return loggers[name]


def add_standard_handlers(logger):
    """
    :type logger: logbook.Logger
    :param logger:
    :return:
    """

    if not configuration["configured"]:
        return

    logger.handlers.append(ColourHandler(
        level=INFO, format_string=configuration["format_string"]
    ))
    logger.handlers.append(NullHandler())


def configure(config):
    if config is not None:
        configuration["format_string"] = config["format_string"]
        configuration["date_format"] = config["date_format"]
        configuration["handlers"] = config["handlers"]

    configuration["configured"] = True

    for logger in loggers.values():
        add_standard_handlers(logger)
