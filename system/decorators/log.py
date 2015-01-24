"""
Logging-related decorators for wrapping functions. Also includes a way
of deprecating things.
"""

import logbook as logging
import traceback
from system.logging import logger as log

__author__ = 'Sean'

_log = log.getLogger(__name__)


def log_message(message, level=None, logger=None, before=True):
    """
    Log a message before or after calling the wrapped function. If logging
    after, the result of the function is passed into the log message for
    formatting as *wrapped_result*.

    :param message: The message to log
    :param level: The level to log at (default: logging.INFO)
    :param logger: The logger to log to (default: generic logger)
    :param before: Log before or after the function call (default: before)
    """

    if level is None:
        level = logging.INFO
    if logger is None:
        logger = _log

    def wrap_func(func):
        if before:
            def wrapper(*args, **kwargs):
                logger.log(level, message)
                return func(*args, **kwargs)
        else:
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                logger.log(level, message, wrapped_result=result)
                return result
        return wrapper
    return wrap_func


def trace(message, *args, **kwargs):
    """
    Convenience function for `log_message` with trace level.

    Args are as for `log_message`, except *level*.
    """

    return log_message(message, logging.TRACE, *args, **kwargs)


def debug(message, *args, **kwargs):
    """
    Convenience function for `log_message` with debug level.

    Args are as for `log_message`, except *level*.
    """

    return log_message(message, logging.DEBUG, *args, **kwargs)


def warn(message, *args, **kwargs):
    """
    Convenience function for `log_message` with warn level.

    Args are as for `log_message`, except *level*.
    """

    return log_message(message, logging.WARNING, *args, **kwargs)


def error(message, *args, **kwargs):
    """
    Convenience function for `log_message` with error level.

    Args are as for `log_message`, except *level*.
    """

    return log_message(message, logging.ERROR, *args, **kwargs)


def critical(message, *args, **kwargs):
    """
    Convenience function for `log_message` with critical level.

    Args are as for `log_message`, except *level*.
    """

    return log_message(message, logging.CRITICAL, *args, **kwargs)


def deprecated(hint_message=None, logger=None):
    """
    Logs a warning message notifying the user that the wrapped function is
    deprecated. A hint message may be supplied to append information on what
    the new way is.

    :param hint_message: Optional help message
    :param logger: Logger to log to (default: generic logger)
    """

    if logger is None:
        logger = _log

    def wrap_func(func):
        msg = "Function usage deprecated: %s" % func.__name__
        if hint_message is not None:
            msg += " - " + hint_message

        def wrapper(*args, **kwargs):
            try:
                logger.warning(
                    msg + "\n" + traceback.format_list(
                        traceback.extract_stack()[-2:-1]
                    )[0].strip()
                )
            except Exception:
                # In case the traceback is derp and the index assumptions break
                logger.warning(msg)
            return func(*args, **kwargs)
        return wrapper
    return wrap_func
