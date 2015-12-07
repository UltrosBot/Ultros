# coding=utf-8

# Found here: http://stackoverflow.com/a/15074754

"""
This is a convenience function for generating random passwords.
You can also run this file directly if you want a 32-length password.
"""

from random import SystemRandom


_random = SystemRandom()


def mkpasswd(length=8, allowed_chars="abcdefghijklmnopqrstuvwxyz"
                                     "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"):
    """
    Create a random password

    Create a random password with the specified length.

    :param length: Number of characters in the password
    :type length: int

    :param allowed_chars: Characters allowed in the password
    :type allowed_chars: str

    :returns: A random password of given length
    :rtype: str
    """

    return "".join(_random.choice(allowed_chars) for x in xrange(length))

if __name__ == "__main__":
    pword = mkpasswd(32)
    print("Random password: %s" % pword)
