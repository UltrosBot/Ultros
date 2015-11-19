# coding=utf-8

import hashlib

from plugins.auth.crypto.algo_base import BaseAlgorithm
from utils.password import mkpasswd

__author__ = 'Gareth Coles'


class HashLibAlgo(BaseAlgorithm):
    def __init__(self, algo):
        self.algo = algo

        try:
            hashlib.new(self.algo)
        except ValueError:
            raise NameError(
                "Unknown or unsupported algorithm: {}".format(algo)
            )

    def check(self, hash, value, salt):
        return hash == self.hash(value, salt)

    def hash(self, value, salt):
        h = hashlib.new(self.algo)
        h.update("{}{}".format(salt, value))
        return h.hexdigest()

    def gen_salt(self):
        allowed = "".join([chr(x) for x in range(0, 255)])
        salt = mkpasswd(64, allowed_chars=allowed)

        h = hashlib.new(self.algo)
        h.update(salt)
        return h.hexdigest()
