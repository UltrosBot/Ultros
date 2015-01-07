__author__ = 'Gareth Coles'

"""
Temporary forwarder module.

See utils.logging.
"""

from utils.logging.logger import getLogger as getLoggerNew

getLogger = getLoggerNew
