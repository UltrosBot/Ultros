from functools import wraps
import Queue
import time

from twisted.internet.defer import Deferred
from twisted.internet.task import LoopingCall
from twisted.python.failure import Failure

from utils import log

__author__ = 'Sean'

_log = log.getLogger(__name__)


class RateLimitExceededError(Exception):
    pass


def _raise_rate_limit_exceeded_error():
    raise RateLimitExceededError("Rate limit exceeded")


class RateLimiter(object):
    def __init__(self, limit=60, buffer=10, time_period=60,
                 delay=None, on_limit=_raise_rate_limit_exceeded_error):
        """
        Limit the rate a function can be called by soft_limit per time_period.
        Can store a buffer of calls to run when limit is available again.
        Returns the result if possible, or a deferred if the function is put in
        the buffer. If you don't want to deal with deferreds, set the buffer to
        0.
        :param limit: Limit of calls per time_period
        :param buffer: Length of backlog
        :param time_period: Time period for limit
        :param delay: Time per check of backlog (default: time_period/limit)
        :param on_limit: Callable to be run on rate limit being reached.
        (default: raise RateLimitExceededError)
        """
        self.soft_limit = limit
        self.buffer = buffer
        self.time_period = float(time_period)
        if delay is None:
            delay = time_period / limit
        self.delay = delay
        self.on_limit = on_limit
        self.last_check = 0
        self.allowance = limit
        self._queue = Queue.Queue(self.buffer)
        self._looping_call = None

    def _update_queue(self):
        try:
            self._update_allowance()
            if self.allowance < 1:
                return
            task = self._queue.get_nowait()
            try:
                result = task[0](*task[1], **task[2])
                # This feels less wrong and but still dirty, but it works.
                if isinstance(result, Deferred):
                    result.chainDeferred(task[3])
                else:
                    task[3].callback(result)
            except:
                _log.debug("Inner exception while updating queue",
                           exc_info=True)
                task[3].errback(Failure())
        except Queue.Empty:
            _log.debug("Queue empty, but looping call still running",
                       exc_info=True)
        except:
            _log.debug("Exception while updating queue", exc_info=True)
        if self._queue.empty():
            self._looping_call.stop()
            self._looping_call = None

    def __call__(self, original_function):
        @wraps(original_function)
        def rate_limited_func(*args, **kwargs):
            result = None
            self._update_allowance()
            # Check allowance
            if self.allowance >= 1:
                result = original_function(*args, **kwargs)
                self.allowance -= 1
            else:
                _log.trace("Soft limit exceeded")
                try:
                    deferred = Deferred()
                    self._queue.put_nowait((original_function,
                                            args,
                                            kwargs,
                                            deferred))
                    if self._looping_call is None:
                        self._looping_call = LoopingCall(self._update_queue)
                        self._looping_call.start(self.delay)
                    result = deferred
                except Queue.Full:
                    # Rate exceeded
                    _log.trace("Hard limit exceeded")
                    if callable(self.on_limit):
                        result = self.on_limit()
            return result

        return rate_limited_func

    def _update_allowance(self):
        # Update allowance
        now = time.time()
        time_passed = now - self.last_check
        self.last_check = now
        self.allowance += time_passed * (self.soft_limit / self.time_period)
        if self.allowance > self.soft_limit:
            self.allowance = self.soft_limit
