# coding=utf-8
"""
    Contains some useful decorators. Remember, plugin commands and hooks are already threaded!
"""

def config(key, value):
    """Decorator that writes to the configuration of the command."""

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
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target = func, args = args, kwargs = kwargs)
        func_hl.start()
        return func_hl

    return async_func