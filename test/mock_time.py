# coding=utf-8

import time as _real_time


__author__ = 'Sean'


class StoppedTime(object):
    """
    An incomplete mock of the time module which doesn't normally pass time.
    Time will only change when sleep() is called. Additionally, sleep() will
    not actually sleep (by default).
    """

    def __init__(self, start_time=None, actually_sleep=False, sleep_time=None):
        """
        :param start_time: Time in seconds to start at (default: time.time())
        :param actually_sleep: Whether to actually sleep when sleep() is called
        :param sleep_time: How long to sleep for (default: passed value)
        """
        if start_time is None:
            start_time = _real_time.time()
        self.__current_time = start_time
        self.__actually_sleep = actually_sleep
        self.__sleep_time = sleep_time

    # StoppedTime functions

    def stoppedtime_set_time(self, value):
        self.__current_time = value

    def stoppedtime_increment_time(self, value):
        self.__current_time += value

    def stoppedtime_decrement_time(self, value):
        self.__current_time -= value

    # Mocked functions

    def sleep(self, value):
        if self.__actually_sleep:
            if self.__sleep_time is not None:
                _real_time.sleep(self.__sleep_time)
            else:
                _real_time.sleep(value)
        self.__current_time += value

    def time(self):
        return self.__current_time
