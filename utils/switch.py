# coding=utf-8

__author__ = 'Gareth Coles'
# Found: http://code.activestate.com/recipes/410692/


class Switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """
        Return the match method once, then stop
        """
        yield self.match, True  # for case, default in switch(x):
        raise StopIteration

    def match(self, *args):
        """
        Indicate whether or not to enter a case suite
        """
        if self.fall or not args:
            return True
        elif self.value in args:  # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False
