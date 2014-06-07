# coding=utf-8

from system.translations import Translations
_ = Translations().get()


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
                raise TypeError(_("%s() takes at most %s non-keyword"
                                  " arguments (%s given)") %
                                (func.__name__, len(argstypes), len(args)))
            argspairs = zip(args, argstypes)
            for k, v in kwargs.items():
                if k not in kwargstypes:
                    raise TypeError(_("Unexpected keyword argument '%s' for "
                                      "%s()") %
                                    (k, func.__name__))
                argspairs.append((v, kwargstypes[k]))
            for param, expected in argspairs:
                if param is not None and not isinstance(param, expected):
                    raise TypeError(_("Parameter '%s' is not %s") %
                                    (param, expected.__name__))
            return func(*args, **kwargs)
        return wrapped
    return wrapper