# coding=utf-8

from __builtin__ import staticmethod

__author__ = 'Sean'


class Perms(object):
    """
    ACL permissions. Names are same as in the Mumble/Murmur source code, except
    pythonised (enum.CamelCaseMembers => class.UPPERCASE_CONSTANTS).
    """

    NONE = 0x0
    WRITE = 0x1
    TRAVERSE = 0x2
    ENTER = 0x4
    SPEAK = 0x8
    MUTE_DEAFEN = 0x10
    MOVE = 0x20
    MAKE_CHANNEL = 0x40
    LINK_CHANNEL = 0x80
    WHISPER = 0x100
    TEXT_MESSAGE = 0x200
    MAKE_TEMP_CHANNEL = 0x400

    # Root channel only
    KICK = 0x10000
    BAN = 0x20000
    REGISTER = 0x40000
    SELF_REGISTER = 0x80000

    CACHED = 0x8000000
    ALL = 0xF07FF

    NAME_TO_PERM = {
        "NONE": NONE,
        "WRITE": WRITE,
        "TRAVERSE": TRAVERSE,
        "ENTER": ENTER,
        "SPEAK": SPEAK,
        "MUTE_DEAFEN": MUTE_DEAFEN,
        "MOVE": MOVE,
        "MAKE_CHANNEL": MAKE_CHANNEL,
        "LINK_CHANNEL": LINK_CHANNEL,
        "WHISPER": WHISPER,
        "TEXT_MESSAGE": TEXT_MESSAGE,
        "MAKE_TEMP_CHANNEL": MAKE_TEMP_CHANNEL,

        "KICK": KICK,
        "BAN": BAN,
        "REGISTER": REGISTER,
        "SELF_REGISTER": SELF_REGISTER,

        "CACHED": CACHED,
        "ALL": ALL
    }

    PERM_TO_NAME = dict((v, k) for (k, v) in NAME_TO_PERM.iteritems())

    @staticmethod
    def has_permission(user_perms, *perms):
        """
        Checks if user_perms has the given permission(s)
        """
        for perm in perms:
            if (user_perms & perm) != perm:
                return False
        return True

    @staticmethod
    def get_permissions(user_perms):
        """
        Get a list of permission values from a permissions int
        """
        perms = []
        for perm in Perms.NAME_TO_PERM.itervalues():
            if (user_perms & perm) == perm:
                perms.append(perm)
        return perms

    @staticmethod
    def get_permissions_names(user_perms):
        """
        Get a list of permission values from a permissions int
        """
        perms = []
        for name, perm in Perms.NAME_TO_PERM.iteritems():
            if (user_perms & perm) == perm:
                perms.append(name)
        return perms

    @staticmethod
    def get_permissions_int(*perms):
        """
        Get the combined form of a collection of permissions
        """
        user_perms = 0
        for perm in perms:
            user_perms |= perm
        return user_perms

# if __name__ == "__main__":
#     from pprint import pprint
#     user_perms = 134219582
#     print "\n=== binary perms ==="
#     print "user_perms".ljust(18), "{0:b}".format(user_perms).zfill(32)
#     for name, perm in Perms.NAME_TO_PERM.iteritems():
#         print name.ljust(18), "{0:b}".format(perm).zfill(32)
#
#     print "\n=== has_permission() ==="
#     for name, perm in Perms.NAME_TO_PERM.iteritems():
#         print name, Perms.has_permission(user_perms, perm)
#
#     print "\n=== get_permissions() ==="
#     pprint(Perms.get_permissions(user_perms))
#
#     print "\n=== get_permissions_names() ==="
#     pprint(Perms.get_permissions_names(user_perms))
#
#     print "\n=== get_permissions_int() ==="
#     print Perms.get_permissions_int(*Perms.get_permissions(user_perms))
#     print "Result is correct?", user_perms == Perms.get_permissions_int(
#         *Perms.get_permissions(user_perms)
#     )
