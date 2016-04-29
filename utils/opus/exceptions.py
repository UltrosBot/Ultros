# coding=utf-8

__author__ = 'Gareth Coles'


class OpusException(Exception):

    def __init__(self, code):
        from utils.opus.lib import opus

        self.code = code
        self.message = opus.opus_strerror(self.code).decode("utf-8")
