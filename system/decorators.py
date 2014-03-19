# coding=utf-8

from functools import wraps
from threading import Thread


def config(key, value):
    """
    Decorator that allows setting a "config" dict for a function.
    """

    def config_inner(func):
        if getattr(func, "config", None) is None:
            func.config = {}
        func.config[key] = value

        return func

    return config_inner


def run_async(func):
    """
         run_async(func)
             function decorator, intended to make "func" run in a separate
             thread (asynchronously).
             Returns the created Thread object

             E.g.:
             @run_async
             def task1():
                 do_something

             @run_async
             def task2():
                 do_something_too

             t1 = task1()
             t2 = task2()
             ...
             t1.join()
             t2.join()
     """

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func


def run_async_daemon(func):
    """
    Much the same as run_async but the thread stops when the app does.
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
    Used to specify type-checking for a function. Some examples..

    class A: pass
    def f(arg1, arg2=None): pass

    @accepts(str, arg2=int)
    @accepts(object, (str, unicode))
    @accepts(object, A)

    This also does a few checks to make sure we're getting the correct number
      of keyword and non-keyword arguments. Remember, if the function defines
      an argument as a keyword, the decorator should too!
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
