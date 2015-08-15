__author__ = 'Gareth Coles'

from enum import Enum


class DefaultDictProxy(object):
    """
    Dict-like wrapper that takes two dicts and checks the second one for a key
    before defaulting to the first one.

    You may also use a dict-like in place of either dict, and you can use the
    `write_to` argument of the initializer to decide which dict/dict-like to
    save changes to, if desired. This defaults to failing silently.
    """

    default_dict = None
    override_dict = None
    write_to = None

    def __init__(self, default_dict, override_dict,
                 write_to=WriteToValues.NONE):
        if write_to not in WriteToValues.members:
            raise ValueError(
                "write_to may only be in {0}".format(WriteToValues.members)
            )

        self.default_dict = default_dict
        self.override_dict = override_dict
        self.write_to = write_to

    def get(self, key, default):
        if key in self.override_dict:
            return self.override_dict[key]

        if key in self.default_dict:
            return self.default_dict[key]

        return default

    def __getitem__(self, item):
        if item in self.override_dict:
            return self.override_dict[item]

        return self.default_dict[item]

    def __setitem__(self, key, value):
        if self.write_to is WriteToValues.NONE:
            return
        elif self.write_to is WriteToValues.RAISE:
            raise AssertionError(
                "Attempted to write to a non-writable DefaultDictProxy"
            )
        elif self.write_to is WriteToValues.DEFAULT:
            self.default_dict[key] = value
        elif self.write_to is WriteToValues.OVERRIDE:
            self.override_dict[key] = value
        else:
            raise ValueError(
                "write_to may only be in {0}".format(WriteToValues.members)
            )


class WriteToValues(Enum):
    RAISE = -1
    PASS = 0
    DEFAULT = 1
    OVERRIDE = 2
