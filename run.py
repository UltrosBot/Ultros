# coding=utf-8

from utils.log import getLogger, open_log, close_log
from system.factory_manager import Manager

open_log("output.log")

logger = getLogger("System")

logger.info("Starting up..")

try:
    manager = Manager()
# reactor.connectTCP(
#     settings["connection"]["host"],
#     settings["connection"]["port"],
#     factory, 120)

finally:
    close_log("output.log")