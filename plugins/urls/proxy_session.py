# coding=utf-8
from txrequests import Session

__author__ = 'Gareth Coles'


class ProxySession(Session):
    def __init__(self, proxies, pool=None, minthreads=1, maxthreads=4, **kwargs):
        super(ProxySession, self).__init__(pool, minthreads, maxthreads,
                                           **kwargs)

        self.proxies = proxies
