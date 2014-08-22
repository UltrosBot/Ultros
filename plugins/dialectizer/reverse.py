# coding=utf-8

"""
rezitcelaid txet-esreveR
"""

__author__ = "Gareth Coles"

from plugins.dialectizer import Dialectizer


class Reverse(Dialectizer):
    """
    rezitcelaid txet-esreveR
    """

    def sub(self, string):
        return string[::-1]
