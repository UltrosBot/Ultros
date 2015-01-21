"""
Some handlers need factory functions to translate configurations. Essentially,
this allows saner user-provided configurations.

These are intended to be supplied instead of classes when adding handlers for
loggers.
"""

__author__ = 'Gareth Coles'

import os
from datetime import timedelta

from pytimeparse.timeparse import timeparse

from logbook import NTEventLogHandler, SyslogHandler
from logbook.queues import ZeroMQHandler, RedisHandler, ThreadedWrapperHandler
from logbook.more import TwitterHandler, ExternalApplicationHandler
from logbook.notifiers import BoxcarHandler, NotifoHandler, PushoverHandler

from logbook.notifiers import create_notification_handler as \
    notification_handler


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


def create_twitter_handler(
        consumer_key=None, consumer_secret=None, username=None, password=None,
        level=0, format_string=None, filter=None, bubble=True
):
    if None in [consumer_key, consumer_secret, username, password]:
        raise ValueError(
            "Consumer key, consumer secret, username and password are "
            "required!"
        )

    return ThreadedWrapperHandler(TwitterHandler(
        consumer_key, consumer_secret, username, password, level,
        format_string, filter, bubble
    ))


def create_external_handler(args=None, format=None, encoding="utf-8", level=0,
                            filter=None, bubble=True):
    if not args:
        raise ValueError("Args are required!")

    return ThreadedWrapperHandler(ExternalApplicationHandler(
        args, format, encoding, level, filter, bubble
    ))


def create_notification_handler(level=0, bubble=True):
    handler = notification_handler("Ultros", level, None)
    handler.bubble = bubble

    return ThreadedWrapperHandler(handler)


def create_boxcar_handler(email=None, password=None, record_limit=None,
                          record_delta=None, level=0, filter=None,
                          bubble=True):
    if None in [email, password]:
        raise ValueError("Email and password are required!")

    if isinstance(record_delta, basestring):
        record_delta = timedelta(seconds=timeparse(record_delta))

    return ThreadedWrapperHandler(BoxcarHandler(
        email, password, record_limit, record_delta, level, filter, bubble
    ))


def create_notifo_handler(username=None, secret=None, record_limit=None,
                          record_delta=None, level=0, filter=None,
                          bubble=True, hide_level=False):
    if None in [username, secret]:
        raise ValueError("Username and secret are required!")

    if isinstance(record_delta, basestring):
        record_delta = timedelta(seconds=timeparse(record_delta))

    return ThreadedWrapperHandler(NotifoHandler(
        "Ultros", username, secret, record_limit, record_delta, level, filter,
        bubble, hide_level
    ))


def create_pushover_handler(apikey=None, userkey=None, device=None, priority=0,
                            sound=None, record_limit=None, record_delta=None,
                            level=0, filter=None, bubble=True):
    if None in [apikey, userkey]:
        raise ValueError("API key and user key are required!")

    if isinstance(record_delta, basestring):
        record_delta = timedelta(seconds=timeparse(record_delta))

    return ThreadedWrapperHandler(PushoverHandler(
        "Ultros", apikey, userkey, device, priority, sound, record_limit,
        record_delta, level, filter, bubble
    ))


def create_zeromq_handler(uri="tcp://127.0.0.1:5000", level=None, filter=None,
                          bubble=True, context=None, multi=True):
    return ZeroMQHandler(uri, level, filter, bubble, context, multi)


def create_redis_handler(host="127.0.0.1", port=6379, key="ultros",
                         extra_fields=None, flush_threshold=128, flush_time=1,
                         level=0, filter=None, password=False, bubble=True,
                         context=None, push_method="rpush"):
    if not extra_fields:
        extra_fields = {}

    return ThreadedWrapperHandler(RedisHandler(
        host, port, key, extra_fields, flush_threshold, flush_time, level,
        filter, password, bubble, context, push_method
    ))
