# coding=utf-8

import time

__author__ = 'Sean'


# TODO: Replace `time` with proper monotonic time
class TokenBucket(object):
    """
    A token bucket. The bucket will be filled with new tokens at a set rate,
    up to a set limit, and code can consume those tokens. If not enough tokens
    are available, the calling code can choose to delay or ignore the operation
    it was about to perform. This is a form of rate limiting.
    """

    def __init__(self, capacity, fill_rate, initial_capacity=None):
        """
        :param capacity: Max token count
        :param fill_rate: Token count increase per second
        :param initial_capacity: Initial token count
        """
        self.capacity = capacity
        self.fill_rate = fill_rate
        if initial_capacity is None:
            initial_capacity = capacity
        self._tokens = initial_capacity
        self._last_fill = time.time()

    def __repr__(self):
        return "%s(capacity=%r, fill_rate=%r, initial_capacity=%r)" % (
            self.__class__.__name__,
            self.capacity,
            self.fill_rate,
            self._tokens
        )

    @property
    def available_tokens(self):
        """
        Number of available tokens. Generally should only be used for debugging
        purposes.
        """
        return self._tokens

    def consume(self, tokens=1):
        """
        Consume tokens from the bucket.
        :param tokens: Number of tokens to consume
        :return: Whether or not there were enough tokens to consume
        """
        self._update_tokens()
        if tokens <= self._tokens:
            self._tokens -= tokens
            return True
        else:
            return False

    def _update_tokens(self):
        """
        Increase token count based on time passed since last fill, up to
        capacity.
        """
        time_passed = time.time() - self._last_fill
        new_tokens = time_passed * self.fill_rate
        self._tokens = min(self._tokens + new_tokens, self.capacity)
