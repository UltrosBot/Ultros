#coding=utf-8
#from system.protocols.irc import constants

"""
IRC utilities and constants, for use with the IRC protocol and plugins
that make direct use of it.
"""

import re
from system.protocols.irc import constants

__author__ = 'rakiru'

_ircformatting = {'BOLD': constants.BOLD,
                  'ITALIC': constants.ITALIC,
                  'COLOUR': constants.COLOUR,
                  'REVERSE': constants.REVERSE,
                  'NORMAL': constants.NORMAL,
                  'CTCP': constants.CTCP}

_irccolours = {'COLOUR_WHITE': constants.COLOUR_WHITE,
               'COLOUR_BLACK': constants.COLOUR_BLACK,
               'COLOUR_BLUE': constants.COLOUR_BLUE,
               'COLOUR_GREEN': constants.COLOUR_GREEN,
               'COLOUR_RED': constants.COLOUR_RED_LIGHT,
               'COLOUR_BROWN': constants.COLOUR_BROWN,
               'COLOUR_PURPLE': constants.COLOUR_PURPLE,
               'COLOUR_ORANGE': constants.COLOUR_ORANGE,
               'COLOUR_YELLOW': constants.COLOUR_YELLOW,
               'COLOUR_GREEN_LIGHT': constants.COLOUR_GREEN_LIGHT,
               'COLOUR_CYAN': constants.COLOUR_CYAN,
               'COLOUR_CYAN_LIGHT': constants.COLOUR_CYAN_LIGHT,
               'COLOUR_BLUE_LIGHT': constants.COLOUR_BLUE_LIGHT,
               'COLOUR_PINK': constants.COLOUR_PINK,
               'COLOUR_GREY': constants.COLOUR_GREY,
               'COLOUR_GREY_LIGHT': constants.COLOUR_GREY_LIGHT}

_ircvalues = dict(_ircformatting, **_irccolours)

_re_formatting = re.compile("(%s[0-9]{1,2})|[%s]" %
                            (constants.COLOUR,
                             ''.join(_ircformatting.values())))


def split_hostmask(hostmask):
    """
    Split a hostmask into its parts and return them.
    :param hostmask: Hostmask to parse
    :return: [user, ident, host]
    :exception Exception: Raised when the hostmask is not in the form "*!*@*"
    """
    posex = hostmask.find(u'!')
    posat = hostmask.find(u'@')
    if posex <= 0 or posat < 3 or posex + 1 == posat or posat + 1 == len(
            hostmask):  # All parts must be > 0 in length
        raise Exception("Hostmask must be in the form '*!*@*'")
    return [hostmask[0:posex], hostmask[posex + 1: posat],
            hostmask[posat + 1:]]


def format_string(value, values=None):
    """
    Used to format an IRC string based on various tokens.
    :param value: The string to format
    :param values: Dictionary of tokens to use for formatting
    :return: Formatted string
    """
    mergedvalues = None
    if values is None:
        mergedvalues = _ircvalues
    else:
        mergedvalues = dict(_ircvalues, **values)
    return value.format(**mergedvalues)


def strip_formatting(message):
    # GOD DAMN MOTHER FUCKER SHIT FUCK CUNT BITCH
    # WHY ARE THE ARGUMENTS BACK TO FRONT?!?
    """
    Why, indeed? Strips IRC formatting codes from message strings.
    :param message: The message string to strip from
    :return: Message string, sans IRC formatting characters
    """
    return _re_formatting.sub("", message)


class IRCUtils(object):
    """
    Because rakiru is a stickler for perfection, sometimes.

    Some things, such as case-mapping, vary per IRCd/server, so
    one-size-fits-all util methods aren't always possible (they can make their
    best attempt, but I'd rather weird bugs didn't pop up due to us glancing
    over something because we didn't have a use-case for it at the time).

    RPL_ISUPPORT 005 NUMERIC: http://www.irc.org/tech_docs/005.html

    CASEMAPPING
    The RFC specifies that {}| are the lowercase versions of []\, due to IRC's
    scandinavian origin. This also implies that ~ is the lowercase of ^, but
    as that's not explicitly stated (although assumed by at least most
    implementations, rfc1459 mode includes this, and strict-rfc1459 doesn't.
    """

    ASCII, RFC1459, STRICT_RFC1459 = xrange(3)
    CASE_MAPPINGS = {"ascii": ASCII,
                     "rfc1459": RFC1459,
                     "strict-rfc1459": STRICT_RFC1459}

    _case_mapping = RFC1459

    def __init__(self, log, case_mapping="rfc1459"):
        self.log = log
        self.case_mapping = case_mapping

    @property
    def case_mapping(self):
        """
        Property for getting our case-mapping.
        :return: Int, the case-mapping.
        """
        return self._case_mapping

    @case_mapping.setter
    def case_mapping(self, val):
        """
        Setter for our case-mapping property.

        We support "ascii", "rfc1459" and "strict-rfc1459" as possible values.
        :param val: A string, the case-mapping to use.
        :return:
        """
        try:
            x = val.lower()
            y = self.CASE_MAPPINGS
            self._case_mapping = y[x]
            # self._case_mapping = self.CASE_MAPPINGS[val.lower()]
        except:
            self.log.warning("Invalid case mapping: %s" % val)

    def lowercase_nick_chan(self, nick):
        """
        Take a nick or channel, make it lowercase.
        :param nick: Nick/channel to make lowercase
        :return: Lowercase nick/channel
        """
        nick = nick.lower()
        if ((self.case_mapping == self.RFC1459 or
             self.case_mapping == self.STRICT_RFC1459)):
            nick = nick.replace('[', '{').replace(']', '}').replace('\\', '|')
            if self.case_mapping == self.RFC1459:
                nick.replace('^', '~')
        return nick

    def compare_nicknames(self, nickone, nicktwo):
        """
        Since lots of string comparisons are case-insensitive, we can
        lower nicks properly using this function.
        :param nickone: First nick to compare
        :param nicktwo: Second nick to compare
        :return: Whether the nicks match, ignoring case
        """
        nickone = self.lowercase_nick_chan(nickone)
        nicktwo = self.lowercase_nick_chan(nicktwo)
        return nickone == nicktwo

    def split_hostmask(self, hostmask):
        """
        Wrapper. Split a hostmask.
        :param hostmask: Hostmask to split.
        :return: [user, ident, host]
        """
        return split_hostmask(hostmask)

    def match_hostmask(self, user, mask):
        """
        Match a user's hostmask with another one. Wildcards are supported.
        :param user: First hostmask to match against
        :param mask: Second hostmask to match against
        :return: Whether the two hostmasks match
        """
        usersplit = split_hostmask(user)
        masksplit = split_hostmask(mask)
        # Case-insensitive match for nickname
        # match_hostmask_part() does a regular lower() too
        # which is fine for the other parts
        usersplit[0] = self.lowercase_nick_chan(usersplit[0])
        masksplit[0] = self.lowercase_nick_chan(masksplit[0])
        for x in xrange(3):
            if not self.match_hostmask_part(usersplit[x], masksplit[x]):
                return False
        return True

    def match_hostmask_part(self, user, mask):
        """
        Uses regex to compare parts of hostmasks. Supports wildcards.
        :param user: First part to match against
        :param mask: Second part to match against
        :return: Whether the two parts match
        """
        # IRC hostmasks can contain two kinds of wildcard:
        #   * - match any character, 0 or more times
        #   ? - match any character, exactly once
        # Here, we convert the mask into its regex counterpart
        # and use that to compare
        mask = re.escape(mask.lower()).replace(r'\*', '.*').replace(r'\?', '.')
        return re.match(mask, user) is not None

    def format_string(self, value, values=None):
        """
        Wrapper. Formats an IRC string using a dict of tokens.
        :param value: String to format
        :param values: Dict of tokens to use for formatting. Optional.
        :return: Formatted string.
        """
        return format_string(value, values)

    def strip_formatting(self, message):
        """
        Wrapper. Remove all IRC formatting characters from a string.
        :param message: String to strip from.
        :return: Stripped string.
        """
        return strip_formatting(message)
