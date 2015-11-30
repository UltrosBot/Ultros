# coding=utf-8
import bcrypt
from kitchen.text.converters import to_bytes

from plugins.auth.crypto.algo_base import BaseAlgorithm

__author__ = 'Gareth Coles'


class BcryptAlgo(BaseAlgorithm):
    def check(self, hash, value, salt=None):
        return hash == self.hash(value, hash)

    def hash(self, value, salt):
        return bcrypt.hashpw(
            to_bytes(value), salt=salt
        )

    def gen_salt(self):
        return bcrypt.gensalt()
