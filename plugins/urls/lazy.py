from txrequests import Session

__author__ = 'Gareth Coles'


class LazyRequest(object):
    result = None

    _args = []
    _kwargs = {}

    def __init__(self, pool=None, minthreads=1, maxthreads=4, req_args=None,
                 req_kwargs=None, session_kwargs=None):
        if not req_args:
            req_args = []
        if not req_kwargs:
            req_kwargs = {}
        if not session_kwargs:
            session_kwargs = {}

        self._args = req_args
        self._kwargs = req_kwargs

        self._session = Session(
            pool=pool, minthreads=minthreads, maxthreads=maxthreads,
            **session_kwargs
        )

    def get(self):
        if self.result is None:
            self.result = self._session.get(*self._args, **self._kwargs)
            del self._session

        return self.result
