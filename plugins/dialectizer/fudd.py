# coding=utf-8
__author__ = "Gareth Coles"

import re
from dialectizer import Dialectizer


class Fudd(Dialectizer):

    subs = ((r'[rl]', r'w'),
            (r'qu', r'qw'),
            (r'th\b', r'f'),
            (r'th', r'd'),
            (r'n[.]', r'n, uh-hah-hah-hah.'))

    def sub(self, string):
        for from_, to_ in self.subs:
            string = re.sub(from_, to_, string)
        return string
