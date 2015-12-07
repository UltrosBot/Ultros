# coding=utf-8

__author__ = 'Gareth Coles'

import string
from numbers import Number


class EmptyStringFormatter(string.Formatter):
    """
    EmptyStringFormatter - The same as the normal string formatter, except
    this one replaces missing tokens with empty strings.

    Use this just like you would a normal formatter. For example:

    >>> formatter = EmptyStringFormatter()
    >>> formatter.format("... {RED} {YELLOW} ...", RED="red")
    '... red  ...'
    """

    def get_value(self, key, args, kwargs):
        try:
            # if hasattr(key, "__mod__"):
            if isinstance(key, Number):
                return args[key]
            else:
                return kwargs[key]
        except (KeyError, IndexError):
            return ""
