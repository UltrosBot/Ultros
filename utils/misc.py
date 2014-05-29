# coding=utf-8

"""
Miscellaneous functions that are used all over the code.
These are used both by the main bot, and the package manager.
"""

__author__ = "Gareth Coles"

import logging
import traceback
import sys

from system.translations import Translations
_ = Translations().get()


def _output_error(logger, error, level):
    if "\n" in error:
        data = error.split("\n")
        for line in data:
            if len(line.strip()) > 0:
                logger.log(level, line)
    else:
        logger.log(level, error)


def output_exception(logger, level=logging.ERROR):
    """
    Utility function for outputting exceptions.
    :param level:  logging level to use for error message.
    :param logger: logging.Logger to use for output
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    data = traceback.format_exception(exc_type, exc_value, exc_traceback)
    _output_error(logger, "".join(data), level)  # "\n".join(data), level)


def chunker(iterable, chunksize):
    """
    Split an iterable into chunks of size `chunksize` and return them in a
    list.
    :param iterable: An iterable to split into chunks
    :param chunksize: The size of the chunks that should be returned
    """
    for i, c in enumerate(iterable[::chunksize]):
        yield iterable[i * chunksize: (i + 1) * chunksize]


def string_split_readable(input, length):
    """
    Convenience function to chunk a string into parts of a certain length,
    whilst being wary of spaces. This means that chunks will only be
    split on spaces, which means some chunks will be shorter, but it also
    means that the resulting list will only contain readable strings.
    :param input: The string to be split
    :param length: Maximum length of the chunks to return
    :return: List containing the split chunks
    :except ValueError: Thrown if there's a word that's longer than the max \
 chunk size.
    """
    done = []
    current = ""
    for word in input.split():
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
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
