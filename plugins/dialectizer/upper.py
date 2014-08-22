# coding=utf-8

"""
UPPERCASE DIALECTIZER
"""

__author__ = "Gareth Coles"

from plugins.dialectizer import Dialectizer


class Upper(Dialectizer):
    """
    UPPERCASE DIALECTIZER
    """

    def sub(self, string):
        return string.upper()
