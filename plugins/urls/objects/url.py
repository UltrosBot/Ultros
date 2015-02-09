__author__ = 'Gareth Coles'


class URL(object):
    protocol = None
    auth = None
    domain = None
    port = None
    path = None

    def __init__(self):
        pass

    def shorten(self, shortener=None, shorten_for=None):
        pass
