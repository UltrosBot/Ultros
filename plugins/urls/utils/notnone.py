__author__ = 'Gareth Coles'


class _NotNone(object):
    def __eq__(self, other):
        return other is not None

    def __ne__(self, other):
        return other is None


NotNone = _NotNone()
