#coding=utf-8
from system.protocols.irc import constants

__author__ = 'rakiru'

import re


def lowercase_nickname(nick):
    return nick.lower().replace(u'{', u'[').replace(u'}', u']')


def compare_nicknames(nickone, nicktwo):
    nickone = lowercase_nickname(nickone)
    nicktwo = lowercase_nickname(nicktwo)
    return nickone == nicktwo


def split_hostmask(hostmask):
    posex = hostmask.find(u'!')
    posat = hostmask.find(u'@')
    if posex <= 0 or posat < 3 or posex + 1 == posat or posat + 1 == len(
            hostmask):  # All parts must be > 0 in length
        raise Exception("Hostmask must be in the form '*!*@*'")
    return [hostmask[0:posex], hostmask[posex + 1: posat],
            hostmask[posat + 1:]]


def match_hostmask_part(user, mask):
    # IRC hostmasks can contain two kinds of wildcard:
    #   * - match any character, 0 or more times
    #   ? - match any character, exactly once
    # Here, we convert the mask into its regex counterpart
    # and use that to compare
    mask = re.escape(mask.lower()).replace(r'\*', '.*').replace(r'\?', '.')
    return re.match(mask, user) is not None


def match_hostmask(user, mask):
    usersplit = split_hostmask(user)
    masksplit = split_hostmask(mask)
    # Case-insensitive match for nickname
    # match_hostmask_part() does a regular lower() too
    # which is fine for the other parts
    usersplit[0] = lowercase_nickname(usersplit[0])
    masksplit[0] = lowercase_nickname(masksplit[0])
    for x in xrange(3):
        if not match_hostmask_part(usersplit[x], masksplit[x]):
            return False
    return True


def format_string(value, values=None):
    ircvalues = {'BOLD' : 'B',
                 'ITALIC' : 'I',
                 'COLOUR' : 'C',
                 'COLOR' : 'C',
                 'REVERSE' : 'R',
                 'NORMAL' : 'N',
                 'CTCP' : 'C'}
    mergedvalues = None
    if values is None:
        mergedvalues = ircvalues
    else:
        mergedvalues = dict(ircvalues, **values)
    return value.format(**mergedvalues)