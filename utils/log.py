# coding=utf-8
__author__ = "Gareth Coles"

import logging
import logging.handlers
import sys
import os


logging.basicConfig(
    format="%(asctime)s | %(name)10s | %(levelname)8s | %(message)s",
    datefmt="%d %b %Y - %H:%M:%S",
    level=(logging.DEBUG if "--debug" in sys.argv else logging.INFO))

loggers = {}


def getLogger(name, path=None,
              fmt="%(asctime)s | %(name)10s | %(levelname)8s | %(message)s",
              datefmt="%d %b %Y - %H:%M:%S", displayname=None):

    if displayname is None:
        displayname = name

    if name in loggers:
        return loggers[name]
    logger = logging.getLogger(displayname)

    if path:
        path = path.replace("..", "")
        path = "logs/" + path
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        handler = logging.FileHandler(path)
        formatter = logging.Formatter(fmt)
        formatter.datefmt = datefmt
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        del handler

    handler = logging.FileHandler("logs/output.log")
    formatter = logging.Formatter(
        "%(asctime)s | %(name)10s | %(levelname)8s | %(message)s")
    formatter.datefmt = "%d %b %Y - %H:%M:%S"
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    del handler

    logger.debug("Created logger.")

    loggers[name] = logger

    return logger


def open_log(path):
    path = path.replace("..", "")
    path = "logs/" + path
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    logger = logging.getLogger("Logging")

    logger.propagate = False

    handler = logging.FileHandler(path)
    formatter = logging.Formatter(
        "%(asctime)s | %(name)10s | %(levelname)8s | %(message)s")
    formatter.datefmt = "%d %b %Y - %H:%M:%S"
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("*** LOGFILE OPENED: %s ***" % path)

    logger.removeHandler(handler)

    del handler
    del logger


def close_log(path):
    path = path.replace("..", "")
    path = "logs/" + path
    if not os.path.exists(os.path.dirname(path)):
        return

    logger = logging.getLogger("Logging")

    logger.propagate = False

    handler = logging.FileHandler(path)
    formatter = logging.Formatter(
        "%(asctime)s | %(name)10s | %(levelname)8s | %(message)s")
    formatter.datefmt = "%d %b %Y - %H:%M:%S"
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("*** LOGFILE CLOSED: %s ***\n\n" % path)
    logger.removeHandler(handler)

    del handler
    del logger
