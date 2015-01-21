__author__ = 'Gareth Coles'

import re

from system.singleton import Singleton
from system.logging.logger import getLogger


class Tokens(object):
    """
    Class for registering tokens.

    A token is a certain pattern in a string which can be replaced with
    something else. For example, we might have a token to insert our username..

    "{USERNAME}"

    This might become "gdude2002" for example, if you're me.

    Of course, we can have more complicated tokens. Let's say we had one for
    adding numbers..

    "{ADD:1:2:3}"

    This might become "6".

    These tokens are found and subsequently parsed using regex.
    """

    __metaclass__ = Singleton

    tokens = {}

    token_regex = None
    parse_regex = None
    escape_regex = None

    def __init__(self):
        self.token_regex = re.compile(r"\{[^}]*\}")
        self.parse_regex = re.compile(r"(?<!\\):")
        self.escape_regex = re.compile(r"\\:")

        self.logger = getLogger("Tokens")

    def get_tokens(self, string):
        return re.findall(self.token_regex, string)

    def add_handler(self, name, func):
        if name not in self.tokens:
            self.tokens[name.upper()] = func

    def remove_handler(self, name):
        name = name.upper()
        if name in self.tokens:
            del self.tokens[name]

    def parse_token(self, string):
        # If string is {STUFF}..
        if string[0] == "{":
            string = string[1:]
        if string[-1] == "}":
            string = string[:-1]

        parts = re.split(self.parse_regex, string)

        return {
            "name": parts[0].upper(),
            "args": parts[1:]
        }

    def replace(self, string):
        tokens = self.get_tokens(string)

        for token in tokens:
            parsed = self.parse_token(token)
            func = self.tokens.get(parsed["name"], None)

            if func is not None:
                args = parsed["args"]
                result = str(func(*args))
                string = string.replace(token, result)

        string = re.sub(self.escape_regex, ":", string)
        return string

    def manual_replace(self, string, name, replace):
        self.logger.info("String: %s" % string)
        self.logger.info("Name: %s" % name)
        self.logger.info("Replace: %s" % replace)

        name = name.upper()
        tokens = self.get_tokens(string)

        for token in tokens:
            parsed = self.parse_token(token)
            if parsed["name"] == name:
                string = string.replace(token, replace)

        return string

    def remove_all(self, string):
        tokens = self.get_tokens(string)

        for token in tokens:
            string = string.replace(token, "")

        return string

if __name__ == "__main__":
    t = Tokens()

    def token_add(args):
        done = 0

        for string in args:
            done += int(string)

        return done

    def token_concat(args):
        done = ""

        for arg in args:
            done += arg

        return done

    t.tokens["ADD"] = token_add
    t.tokens["CONCAT"] = token_concat

    print t.replace(
        "{ADD:1:2:3:4:5}, {ADD:1:2:3}, {CONCAT:abc:def:\:: letters} :other "
        "stuff that shouldn't be parsed: {}"
    )
