#!/usr/bin/env python
# coding=utf-8

"""
Ultros - That squidoctopus bot thing.

This is the main file - You run this! Importing it is a bad idea!
Stuff like that!

Don't forget to read the README, the wiki and the LICENSE before you even
consider modifying or distributing this software.

If, however, you do fork yourself a copy and make some changes, submit a
pull request or otherwise get in contact with us - we'd love your help!
"""

import os
import sys
from kitchen.text.converters import getwriter

if __name__ == "__main__":
    if os.path.dirname(sys.argv[0]):
        os.chdir(os.path.dirname(sys.argv[0]))

    from utils.log import getLogger, open_log, close_log
    from utils.misc import output_exception
    from system.factory_manager import Manager

    sys.stdout = getwriter('utf-8')(sys.stdout)
    sys.stderr = getwriter('utf-8')(sys.stderr)

    if not os.path.exists("logs"):
        os.mkdir("logs")

    open_log("output.log")

    logger = getLogger("System")

    logger.info("Starting up..")

    manager = None

    try:
        manager = Manager()

    except Exception:
        logger.critical("Runtime error - process cannot continue!")
        output_exception(logger)

    finally:
        try:
            manager.unload()
            close_log("output.log")

            raw_input("Press enter to exit.")
        except:
            pass
