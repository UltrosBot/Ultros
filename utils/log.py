__author__ = 'Gareth Coles'

"""
Temporary forwarder module.

See system.logging
"""

from system.decorators.log import deprecated as __deprecated
from system.logging import logger

getLogger = __deprecated("Import from system.logging")(logger.getLogger)
