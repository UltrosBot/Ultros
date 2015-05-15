"""
Logbook-based logging, modified a bit to suit our purposes.

Logbook turned out to be fairly complicated. Who knew? Still, it adds a lot
of things to the logging system that would have been a huge pain to do
ourselves, and our new logging system allows plugins to modify various aspects
of logging, as well as provide additional handlers.

For custom handlers, you may either edit the `configuration` defined in this
module with something loaded from your plugin's config, or you can require
that your users do their configuration in the main **logging.yml** file. It's
up to you.
"""

__author__ = 'Gareth Coles'

from kitchen.text.converters import to_unicode

# This does the magic - let's make logbook more suitable for us
import system.logging.shim as shim

# Handlers
from logbook import NullHandler, TimedRotatingFileHandler
# Levels
from logbook import NOTSET, INFO

# Moar handlers
from system.logging.handlers.builders import create_syshandler, \
    create_boxcar_handler, create_external_handler, \
    create_notification_handler, create_notifo_handler, \
    create_pushover_handler, create_twitter_handler, \
    create_redis_handler, create_zeromq_handler, create_metrics_handler, \
    create_mail_handler
from system.logging.handlers.colours import ColourHandler


def get_level_from_name(name):
    """
    Get a logging level from a string - For example, "INFO".
    """

    if not isinstance(name, basestring):
        return name

    name = name.upper()

    return shim.reverse_level_names.get(name)


#: Default handler list
defaults = [
    "boxcar", "notifo", "pushover", "email", "redis", "system", "colour",
    "zeromq", "notification", "twitter", "external", "file", "metrics", "null"
]

#: Storage for the configuration of each handler
configuration = {
    "format_string": u"{record.time:%b %d %Y - %H:%M:%S} | "
                     u"{record.channel:>25} | {record.level_name:<8} | "
                     u"{record.message}",
    "handlers": {
        "boxcar": False,
        "email": False,
        "external": False,
        "notification": False,
        "redis": False,
        "system": False,
        "twitter": False,

        # Constants, these usually won't need to be changed or configured.
        "colour": True,
        "file": [
            "logs/output.log", "a", "utf-8", INFO,
            (
                u"{record.time:%b %d %Y - %H:%M:%S} | "
                u"{record.channel:>25} | {record.level_name:<8} | "
                u"{record.message}"
            ), "%Y-%m-%d", 30, None, True
        ],
        "metrics": True,
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

    "boxcar": create_boxcar_handler,
    "email": create_mail_handler,
    "external": create_external_handler,
    "notification": create_notification_handler,
    "notifo": create_notifo_handler,
    "pushover": create_pushover_handler,
    "redis": create_redis_handler,
    "twitter": create_twitter_handler,
    "zeromq": create_zeromq_handler,

    "colour": ColourHandler,
    "file": TimedRotatingFileHandler,
    "null": NullHandler,
    "system": create_syshandler,
    "metrics": create_metrics_handler
}

# The order handlers should be added to loggers
handler_order = [
    "boxcar", "notifo", "pushover", "email", "redis", "zeromq",
    "notification", "twitter", "external", "system", "file", "colour",
    "metrics", "null"
]


def shorten_name(name):
    """
    Shorten a name so that it fits within our standard 25-char limit.

    If it contains dots, then it'll be collapsed around them as necessary
    before possibly being truncated.

    >>> shorten_name("ThisIsAVeryVeryVeryVeryVeryLongName")
    'ThisIsAVeryVeryVeryVeryV~'
    >>> shorten_name("this.is.also.a.pretty.long.name")
    't.i.a.a.p.l.name'
    """

    if len(name) > 25:
        if "." in name:
            parts = name.split(".")
            last = parts.pop()

            done = ""

            for x in parts:
                done += x[0]
                done += "."

            done += last

            if len(done) > 25:
                done = done[:24] + "~"

            name = done
        else:
            name = name[:24] + "~"

    return name


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
    name = shorten_name(name)

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

                if "level" in config:
                    config["level"] = get_level_from_name(config["name"])

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
                    format_string=configuration["format_string"],
                    bubble=True
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
    :type config: dict, Config, None
    """

    if config is not None:
        configuration["format_string"] = config.get(
            "format_string", to_unicode(configuration["format_string"])
        )
        configuration["handlers"] = config.get(
            "handlers", configuration["handlers"]
        )
        configuration["level"] = get_level_from_name(
            config.get("level", configuration["level"])
        )

        configuration["handlers"].update({
            # Constants
            "colour": True,
            "file": [
                "logs/output.log", "a", "utf-8", configuration["level"],
                configuration["format_string"], "%Y-%m-%d", 30, None, True
            ],
            "metrics": True,
            "null": [NOTSET]
        })

    configuration["configured"] = True

    for logger in loggers.values():
        add_all_handlers(logger)

    getLogger("Logging").info("    ")
    getLogger("Logging").info("    === Logging session opened ===")
    getLogger("Logging").info("    ")

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
