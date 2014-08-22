# coding=utf-8
"""
Various threading-related decorators. These allow you to use the threadpool.
"""

from functools import wraps
from threading import Thread

from twisted.python.threadpool import ThreadPool

from system.decorators.log import deprecated
from system.translations import Translations
_ = Translations().get()

pool = ThreadPool(name="Decorators")


@deprecated("Use run_async_threadpool instead.")
def run_async(func):
    """
    Function decorator to run in a normal thread.

    These threads **will not be stopped** with Ultros; if you want them to be
    stopped then use the `run_async_daemon` function.

    Functions that are decorated will return their Thread, which you can use
    as normal. For example::

        @run_async
        def func():
            # Something that takes forever to run
            pass

        t1 = func()
        # Something else that takes some time
        t1.join()
    """

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func


@deprecated("Use run_async_threadpool instead.")
def run_async_daemon(func):
    """
    Function decorator to run in a daemon thread.

    These threads **will** be stopped with Ultros.

    Functions that are decorated will return their Thread, which you can use
    as normal. For example::

        @run_async_daemon
        def func():
            # Something that takes forever to run
            pass

        t1 = func()
        # Something else that takes some time
        t1.join()
    """

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.daemon = True
        func_hl.start()
        return func_hl

    return async_func


def run_async_threadpool(func):
    """
    Function decorator to run in a a thread from the threadpool.

    These threads are run using a special threadpool which is only used for
    decorators. You will not be able to join these threads, nor will you
    be able to assign callbacks to them.

    For example::

        @run_async_threadpool
        def func():
            # Something that takes forever to run
            pass
    """

    @wraps(func)
    def async_func(*args, **kwargs):
        if not pool.started:
            pool.start()

        return pool.callInThread(func, *args, **kwargs)

    return async_func


def run_async_threadpool_callback(cb):
    """
    Function decorator to run in a a thread from the threadpool, with a
    callback on completion.

    These threads are run using a special threadpool which is only used for
    decorators (the same one `run_async_threadpool` uses). The callback
    function will be called with the following parameters:

    * success: True if the call succeeded, false otherwise
    * result: Whatever the call returned, or a Failure if it didn't succeed

    Your callback **must not block** and should perform as little work as
    possible. For example, a very common use is to schedule a Deferred to
    fire in the main reactor thread using **.callFromThread**.

    Note that the callback is run from the separate thread, not the main
    reactor thread.

    For example::

        def cb(success, result):
            if success:
                print "Success: %s" % result
            else:
                print "Failure: %s" % result

        @run_async_threadpool_callback(cb)
        def func():
            # Something that takes forever to run
            pass

    :param cb: The callback to run when the wrapped function completes.
    :type cb: function
    """

    def inner(func):

        @wraps(func)
        def async_func(*args, **kwargs):
            if not pool.started:
                pool.start()
            return pool.callInThreadWithCallback(cb, func, *args, **kwargs)

        return async_func

    return inner
