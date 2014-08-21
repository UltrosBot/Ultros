# coding=utf-8

"""Reverse-text dialectizer"""

__author__ = "Gareth Coles"

from plugins.dialectizer import Dialectizer


class Reverse(Dialectizer):
    """Reverse-text dialectizer"""

    def sub(self, string):
        return string[::-1]
