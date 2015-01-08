__author__ = 'Gareth Coles'

"""
Temporary forwarder module.

See utils.logging.
"""

from system.logging.logger import getLogger as getLoggerNew

getLogger = getLoggerNew
