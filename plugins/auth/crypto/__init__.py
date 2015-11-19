# coding=utf-8

try:
    from plugins.auth.crypto.algo_bcrypt import BcryptAlgo
except ImportError:
    BcryptAlgo = None

from plugins.auth.crypto.algo_hashlib import HashLibAlgo
from plugins.auth.crypto.algo_pbkdf2 import PBKDF2Algo

__author__ = 'Gareth Coles'

banned_algos = [
    "md4", "md5", "sha", "sha1",
]


def get_algo(name):
    """
    :rtype: algo_base.BaseAlgorithm
    """
    if name.lower() == "bcrypt":
        if not BcryptAlgo:
            raise ImportError("Unable to import bcrypt")
        return BcryptAlgo()

    elif name.lower() == "pbkdf2":
        return PBKDF2Algo()
    elif name.lower() in banned_algos:
        raise NameError("Insecure algorithm: {}".format(name))
    else:
        return HashLibAlgo(name)
