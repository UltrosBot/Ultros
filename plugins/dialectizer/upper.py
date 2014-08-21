# coding=utf-8

"""Uppercase dialectizer"""

__author__ = "Gareth Coles"

from plugins.dialectizer import Dialectizer


class Upper(Dialectizer):
    """Uppercase dialectizer"""

    def sub(self, string):
        return string.upper()
