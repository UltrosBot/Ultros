# coding=utf-8

__author__ = 'Gareth Coles'


class BaseAlgorithm(object):
    def hash(self, value, salt):
        pass

    def check(self, hash, value, salt):
        return hash == self.hash(value, salt)

    def gen_salt(self):
        pass
