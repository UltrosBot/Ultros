# coding=utf-8
import string
from numbers import Number

__author__ = 'Gareth Coles'

FILENAME_SAFE_CHARS = (
    "/\\-_.()#" +
    string.digits +
    string.letters +
    string.whitespace
)


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


def to_filename(_string):
    return filter(
        lambda x: x in FILENAME_SAFE_CHARS,
        _string
    )
