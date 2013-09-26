# coding=utf-8


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    Limitations: The decorated class cannot be inherited from.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


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