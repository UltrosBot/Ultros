import socket
from twisted.internet import defer, reactor
from twisted.python.threadpool import ThreadPool

__author__ = 'Gareth Coles'


class AddressResolver(object):
    pool = None

    def __init__(self, minthreads=1, maxthreads=4):
        self.pool = ThreadPool(minthreads=minthreads, maxthreads=maxthreads)
        # unclosed ThreadPool leads to reactor hangs at shutdown
        # this is a problem in many situation, so better enforce pool stop here
        reactor.addSystemEventTrigger(
            "before", "shutdown", lambda: self.pool.stop()
        )

        self.pool.start()

    def get_host_by_name(self, address):
        def func():
            try:
                reactor.callFromThread(
                    d.callback, socket.gethostbyname(address)
                )
            except Exception as e:
                reactor.callFromThread(d.errback, e)

        d = defer.Deferred()
        self.pool.callInThread(func)
        return d

    def close(self):
        self.pool.stop()
