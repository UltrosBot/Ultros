# coding=utf-8

"""
Miscellaneous functions that are used all over the code.
These are used both by the main bot, and the package manager.
"""

__author__ = "Gareth Coles"

import os
import os.path

import re
from system.translations import Translations
_ = Translations().get()


current_location = os.path.abspath(os.curdir)


def _output_error(logger, error, level):
    if "\n" in error:
        data = error.split("\n")
        for line in data:
            if len(line.strip()) > 0:
                logger.log(level, line)
    else:
        logger.log(level, error)


def valid_path(path):
    if os.name == "nt":
        path = path.replace("/", "\\")

    request = os.path.relpath(path, current_location)
    request = os.path.abspath(request)

    common = os.path.commonprefix([request, current_location])

    return common.startswith(current_location)


def dict_swap(d):
    """
    Swap dictionary keys and values.

    :type d: dict
    """

    done = {}
    for k, v in d.items():
        done[v] = k

    return done


def chunker(iterable, chunksize):
    """
    Split an iterable into chunks of size *chunksize* and return them in a
    list.

    :param iterable: An iterable to split into chunks
    :param chunksize: The size of the chunks that should be returned
    """

    for i, c in enumerate(iterable[::chunksize]):
        yield iterable[i * chunksize: (i + 1) * chunksize]


def string_split_readable(inp, length):
    """
    Convenience function to chunk a string into parts of a certain length,
    whilst being wary of spaces.

    This means that chunks will only be split on spaces, which means some
    chunks will be shorter, but it also means that the resulting list will
    only contain readable strings.

    ValueError is thrown if there's a word that's longer than the max chunk
    size.

    :param inp: The string to be split
    :param length: Maximum length of the chunks to return
    :return: List containing the split chunks
    """

    done = []
    current = ""
    for word in inp.split():
        if len(current) == length:
            done.append(current)
            current = ""

        if len(word) > length:
            raise ValueError(_("Word %s is longer than %s characters") %
                              (word, length))
        else:
            if len(current + word) > length:
                done.append(current)
                current = ""
            current += word

        if len(current) <= (length - 1):
            current += " "

    if len(current):
        done.append(current)

    return done


class AttrDict(dict):
    """Simple attribute dictionary.

    Simply, dictionary keys are also available as properties. Otherwise, this
    is functionally equivalent to a dict.
    """

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class AutoVivificationDict(dict):
    """Auto-vivification, like Perl. Any time a value is missing, a new
    AutoVivificationDict is created and added in place.

    Using defaultdict would make more sense in most circumstances, but
    sometimes you just want dicts in dicts in dicts.
    """
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


flags = {
    "d": re.DEBUG,
    "i": re.IGNORECASE,
    "l": re.LOCALE,
    "m": re.MULTILINE,
    "s": re.DOTALL,
    "u": re.UNICODE,
    "x": re.VERBOSE,
}


def str_to_regex_flags(string):
    """Get a set of regex flags for an input string.

    The supported flags are each of "dilmsux".

    * *d* - Debug
    * *i* - Ignore case
    * *l* - Locale dependency
    * *m* - Multi-line *^* and *$*
    * *s* - Make *.* match newlines
    * *u* - Unicode dependency
    * *x* - Verbose (pretty) regexes

    :param string: The string of flags
    :type string: str

    :return: The OR'd set of regex flags
    :rtype: int
    """

    string = string.lower()

    result = 0

    for x in string:
        result |= flags[x]

    return result
