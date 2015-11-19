# coding=utf-8

from plugins.auth.crypto.algo_base import BaseAlgorithm

from pbkdf2 import crypt

__author__ = 'Gareth Coles'


class PBKDF2Algo(BaseAlgorithm):
    def check(self, hash, value, salt=None):
        return hash == self.hash(value, hash)

    def hash(self, value, salt=None):
        return crypt(
            value, salt=salt, iterations=400
        )

    def gen_salt(self):
        return None  # It's in the hash
