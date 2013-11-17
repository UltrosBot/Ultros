#coding=utf-8
#from system.protocols.irc import constants
import re
from system.protocols.irc import constants

__author__ = 'rakiru'


def split_hostmask(hostmask):
    posex = hostmask.find(u'!')
    posat = hostmask.find(u'@')
    if posex <= 0 or posat < 3 or posex + 1 == posat or posat + 1 == len(
            hostmask):  # All parts must be > 0 in length
        raise Exception("Hostmask must be in the form '*!*@*'")
    return [hostmask[0:posex], hostmask[posex + 1: posat],
            hostmask[posat + 1:]]


def format_string(value, values=None):
    ircvalues = {'BOLD': constants.bold,
                 'ITALIC': constants.italic,
                 'COLOUR': constants.colour,
                 'COLOR': constants.color,
                 'REVERSE': constants.reverse,
                 'NORMAL': constants.normal,
                 'CTCP': constants.ctcp}
    mergedvalues = None
    if values is None:
        mergedvalues = ircvalues
    else:
        mergedvalues = dict(ircvalues, **values)
    return value.format(**mergedvalues)


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

    def __init__(self, log, case_mapping="rfc1459"):
        self.log = log
        self.case_mapping = case_mapping

    @property
    def case_mapping(self):
        return self._case_mapping

    @case_mapping.setter
    def case_mapping(self, val):
        try:
            x = val.lower()
            y = self.CASE_MAPPINGS
            self._case_mapping = y[x]
            # self._case_mapping = self.CASE_MAPPINGS[val.lower()]
        except:
            self.log.warning("Invalid case mapping: %s" % val)

    def lowercase_nick_chan(self, nick):
        nick = nick.lower()
        if ((self.case_mapping == self.RFC1459 or
             self.case_mapping == self.STRICT_RFC1459)):
            nick = nick.replace('[', '{').replace(']', '}').replace('\\', '|')
            if self.case_mapping == self.RFC1459:
                nick.replace('^', '~')
        return nick

    def compare_nicknames(self, nickone, nicktwo):
        nickone = self.lowercase_nick_chan(nickone)
        nicktwo = self.lowercase_nick_chan(nicktwo)
        return nickone == nicktwo

    def split_hostmask(self, hostmask):
        return split_hostmask(hostmask)

    def match_hostmask(self, user, mask):
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
        # IRC hostmasks can contain two kinds of wildcard:
        #   * - match any character, 0 or more times
        #   ? - match any character, exactly once
        # Here, we convert the mask into its regex counterpart
        # and use that to compare
        mask = re.escape(mask.lower()).replace(r'\*', '.*').replace(r'\?', '.')
        return re.match(mask, user) is not None

    def format_string(self, value, values=None):
        return format_string(value, values)
