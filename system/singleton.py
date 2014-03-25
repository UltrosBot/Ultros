__author__ = 'Gareth Coles'

# Found: http://stackoverflow.com/a/6798042/2524563


class Singleton(type):
    """
    Metaclass for creating classes that will only ever have one instance.

    Use it by doing:

    >>> class Classname(object):
    ...     __metaclass__ = Singleton
    ...
    >>> x = Classname()
    >>> y = Classname()
    >>> x is y
    True

    Your class will automatically be a singleton, you do not need to call
    **instance()** or any other special function.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]
