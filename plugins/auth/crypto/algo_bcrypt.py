# coding=utf-8

from plugins.auth.crypto.algo_base import BaseAlgorithm

import bcrypt

__author__ = 'Gareth Coles'


class BcryptAlgo(BaseAlgorithm):
    def check(self, hash, value, salt=None):
        return hash == self.hash(value, hash)

    def hash(self, value, salt):
        return bcrypt.hashpw(
            value, salt=salt
        )

    def gen_salt(self):
        return bcrypt.gensalt()
