# coding=utf-8

"""Lowercase dialectizer"""

__author__ = "Gareth Coles"

from plugins.dialectizer import Dialectizer


class Lower(Dialectizer):
    """Lowercase dialectizer"""

    def sub(self, string):
        return string.lower()
