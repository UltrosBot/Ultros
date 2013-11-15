__author__ = 'Sean'


class Rank(object):
    """
    A user rank in a channel.
    We're all consenting adults here: don't change the properties after
    creation please, or tentacles will go the wrong way.

    Note: A higher order means a lower rank, and vice-versa. This class
    overrides certain operators, and does so in terms of rank, not order.
    i.e. Rank("o","@","2") > Rank("v","+","5") == True
    """
    def __init__(self, mode, symbol, order):
        self.mode = mode
        self.symbol = symbol
        self.order = order

    def __str__(self):
        return "%s%s%s" % (self.mode, self.symbol, self.order)

    def __lt__(self, other):
        return self.order > other.order

    def __gt__(self, other):
        return self.order < other.order

    def __le__(self, other):
        return self.order >= other.order

    def __ge__(self, other):
        return self.order <= other.order

    def __eq__(self, other):
        return self.order == other.order

    def __ne__(self, other):
        return self.order != other.order

class Ranks(object):
    def __init__(self):
        self._ranks_by_mode = {}
        self._ranks_by_symbol = {}
        self._ranks_by_order = {}

    def add_rank(self, rank_or_mode, symbol=None, order=None):
        if not isinstance(rank_or_mode, Rank):
            if symbol is None or order is None:
                raise ValueError("First argument must be of type Rank or all "
                                 "arguments must be given")
            else:
                rank_or_mode = Rank(rank_or_mode, symbol, order)
        self._ranks_by_mode[rank_or_mode.mode] = rank_or_mode
        self._ranks_by_symbol[rank_or_mode.symbol] = rank_or_mode
        self._ranks_by_order[rank_or_mode.order] = rank_or_mode

    @property
    def modes(self):
        return self._ranks_by_mode.keys()

    @property
    def symbols(self):
        return self._ranks_by_symbol.keys()

    @property
    def orders(self):
        return self._ranks_by_order.keys()

    def by_mode(self, mode):
        return self._ranks_by_mode[mode]

    def by_symbol(self, symbol):
        return self._ranks_by_symbol[symbol]

    def by_order(self, order):
        return self._ranks_by_order[order]

    def is_op(self, rank, or_above=True):
        op = self.by_mode("o")
        if or_above:
            return rank >= op
        else:
            return rank == op

    def is_voice(self, rank, or_above=True):
        voice = self.by_mode("v")
        if or_above:
            return rank >= voice
        else:
            return rank == voice
