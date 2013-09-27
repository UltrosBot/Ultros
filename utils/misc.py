# coding=utf-8
__author__ = "Gareth Coles"

import logging
import traceback
import sys


def _output_error(logger, error, level):
    if "\n" in error:
        data = error.split("\n")
        for line in data:
            if len(line.strip()) > 0:
                logger.log(level, line)
    else:
        logger.log(level, error)


def output_exception(logger, level=logging.ERROR):
    """
    Utility function for outputting exceptions.
    :param level:  logging level to use for error message.
    :param logger: logging.Logger to use for output
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    data = traceback.format_exception(exc_type, exc_value, exc_traceback)
    _output_error(logger, "".join(data), level)  # "\n".join(data), level)
