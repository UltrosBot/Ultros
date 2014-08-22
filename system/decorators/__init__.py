"""Various extremely useful decorators, covering a good deal of functionality.

* Filter: function type-checking, if you really need it
* Log: Logging and deprecation decorators
* Rate limit: Rate-limiting designed for API calls
* Threads: Decorators for running things in the threadpool
"""

__author__ = 'Sean'

# Deprecated imports, to support old decorator usage
from .filter import accepts
from .threads import run_async, run_async_daemon, run_async_threadpool,\
    run_async_threadpool_callback
from .log import deprecated as __deprecated

accepts = __deprecated("Import from decorators.filter")(accepts)
run_async = __deprecated("Import from decorators.threads")(run_async)
run_async_daemon = __deprecated("Import from decorators.threads")(
    run_async_daemon)
run_async_threadpool = __deprecated("Import from decorators.threads")(
    run_async_threadpool)
run_async_threadpool_callback = __deprecated("Import from decorators.threads")(
    run_async_threadpool_callback)

__all__ = ["threads",
           "filters",
           "ratelimit",
           "log",
           # Deprecated references, as above
           "accepts",
           "run_async",
           "run_async_daemon",
           "run_async_threadpool",
           "run_async_threadpool_callback"]
