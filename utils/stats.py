# coding=utf-8

"""
Utilities for recording and aggregating stats
"""

__author__ = 'Sean'

from itertools import ifilter
import time


def inc(value):
    return value + 1


def dec(value):
    return value - 1


class TimeDataAggregator(object):

    _TIME = 0
    _VALUE = 1

    def __init__(self, time_period, saved_periods, initial_value=0,
                 increment_function=None, decrement_function=None):
        """
        Initialize the timed data aggregator.

        *increment_function* and *decrement_function* must accept one argument
        (the value) and return the incremented value. The defaults will +/- 1.

        :param time_period: Individual time slice to record a value for
        :param saved_periods: Number of time slices to save
        :param initial_value: Initial value of new time slices (default: 0)
        :param increment_function: Function to increment value (default: += 1)
        :param decrement_function: Function to decrement value (default: -= 1)
        """

        self.TIME_PERIOD = time_period
        self.SAVED_PERIODS = saved_periods
        self.initial_value = initial_value

        if increment_function is None:
            increment_function = inc
        self._increment_function = increment_function

        if decrement_function is None:
            decrement_function = dec
        self._decrement_function = decrement_function

        self._records = [None] * self.SAVED_PERIODS
        for _x in xrange(self.SAVED_PERIODS):
            self._records[_x] = [0, self.initial_value]

        self._index = 0
        self._last_index = self.SAVED_PERIODS - 1

    def _get_current_record(self):
        """
        Get the current record. Creates a new record for current time-slot if
        necessary.

        :return: The current record
        """

        time_slot = int(time.time() / self.TIME_PERIOD)
        # Check if we need to create a new record
        if self._records[self._index][self._TIME] != time_slot:
            # Create a new record and reset the data
            self._last_index = self._index
            self._index = (self._index + 1) % self.SAVED_PERIODS
            self._records[self._index][self._TIME] = time_slot
            self._records[self._index][self._VALUE] = 0

        return self._records[self._index]

    def _get_last_record(self):
        """
        Get the previous record (the latest one that's fully passed).

        Creates a new record for current time-slot if necessary.

        :return: The previous record
        """

        # Call _get_current_record to update index and records if necessary
        self._get_current_record()
        return self._records[self._last_index]

    def increment(self):
        """
        Increment the stored value for the current record.

        Uses the passed in increment_function.
        """

        record = self._get_current_record()
        record[self._VALUE] = self._increment_function(record[self._VALUE])

    def decrement(self):
        """
        Decrement the stored value for the current record.

        Uses the passed in decrement_function.
        """

        record = self._get_current_record()
        record[self._VALUE] = self._decrement_function(record[self._VALUE])

    def _sieve(self, record):
        """
        Filter function to remove unused records.

        Defined here to avoid defining on every call to get_records().

        :param record:
        """

        return record[self._TIME] != 0

    def _time_fixer(self, record):
        """
        Convert time slot (record[_TIME]) to time stamp (time.time()), and
        return a tuple of the fixed record.

        Defined here to avoid defining on every call to get_records().

        :param record: The record to be "fixed"
        :return: A tuple version of record, with fixed time
        :rtype: tuple
        """

        return record[self._TIME] * self.TIME_PERIOD, record[self._VALUE]

    def get_records(self, include_latest=True):
        """
        Gets a copy of all current records.

        :return: A list of tuples of form (timestamp, value)
        :rtype: list
        """

        start = self._index + 1
        end = self._index + self.SAVED_PERIODS
        if include_latest:
            end += 1
        return map(
            self._time_fixer,
            ifilter(
                self._sieve,
                (
                    self._records[x % self.SAVED_PERIODS]
                    for x in xrange(start, end)
                )
            )
        )

    def get_latest(self):
        """
        Gets the latest record.

        :return: The latest record
        """

        record = self._get_current_record()
        return record[self._TIME] * self.TIME_PERIOD, record[self._VALUE]

    def get_latest_complete(self):
        """
        Gets the latest complete record.

        :return: The latest complete record
        """

        record = self._get_last_record()
        return record[self._TIME] * self.TIME_PERIOD, record[self._VALUE]
