# coding=utf-8

from functools import wraps
from threading import Thread


def run_async(func):
    """
    A function decorator intended to cause the function to run in another
    thread (in other words, asynchronously).

    These threads **will not be stopped** with Ultros; if you want them to be
    stopped then use the **run_async_daemon** function.

    Functions that are decorated will return their Thread, which you can use
    as normal. For example::

        @run_async
        def func():
            # Something that takes forever to run
            pass

        t1 = func()
        # Something else that takes some time
        t1.join()

    :param func: The function to decorate
    :type func: function
    """

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func


def run_async_daemon(func):
    """
    A function decorator intended to cause the function to run in another
    thread (in other words, asynchronously).

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

    :param func: The function to decorate
    :type func: function
    """

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.daemon = True
        func_hl.start()
        return func_hl

    return async_func

# Yeah, I know how non-Pythonic the `accepts` decorator is, but it's
#   somewheat necessary to help new Python devs get into working with
#   the plugin system, especially if they come from a non-Python background.

# The decorator was found at the following URL:
#   http://blog.mathieu-leplatre.info/python-check-arguments-types.html


def accepts(*argstypes, **kwargstypes):
    """
    A rather un-pythonic decorator that we haven't yet found a use for.

    Used to specify type-checking for a function. Some examples::

        class A:
            pass

        @accepts(str, arg2=int)
        def f(arg1, arg2=None):
            pass

        @accepts(object, (str, unicode))
        def f(arg1, arg2):
            pass

        @accepts(object, A)
        def f(arg1, arg2):
            pass

    This also does a few checks to make sure we're getting the correct number
    of keyword and non-keyword arguments. Remember, if the function defines
    an argument as a keyword, the decorator should too!

    :param argstypes: The types 
    """

    def wrapper(func):
        def wrapped(*args, **kwargs):
            if len(args) > len(argstypes):
                raise TypeError("%s() takes at most %s non-keyword arguments "
                                "(%s given)" % (func.__name__, len(argstypes),
                                                len(args)))
            argspairs = zip(args, argstypes)
            for k, v in kwargs.items():
                if k not in kwargstypes:
                    raise TypeError("Unexpected keyword argument '%s' for %s()"
                                    % (k, func.__name__))
                argspairs.append((v, kwargstypes[k]))
            for param, expected in argspairs:
                if param is not None and not isinstance(param, expected):
                    raise TypeError("Parameter '%s' is not %s"
                                    % (param, expected.__name__))
            return func(*args, **kwargs)
        return wrapped
    return wrapper
