#!/usr/bin/env python
# coding=utf-8

###                  === BEGIN LICENSE BLOCK ===                  ###
###                                                               ###
### Ultros is distributed under the Artistic License 2.0.         ###
### You should have received a copy of this license with Ultros,  ###
### but if you didn't, you can find one at the following link:    ###
###                                                               ###
###          http://choosealicense.com/licenses/artistic/         ###
###                                                               ###
###                  ===  END LICENSE BLOCK  ===                  ###

"""
Ultros - That squidoctopus bot thing.

This is the main file - You run this! Importing it is a bad idea!
Stuff like that!

Don't forget to read the README, the wiki and the LICENSE before you even
consider modifying or distributing this software.

If, however, you do fork yourself a copy and make some changes, submit a
pull request or otherwise get in contact with us - we'd love your help!
"""

import logging
import os
import sys

from kitchen.text.converters import getwriter

if "--update" in sys.argv:
    try:
        print "Attempting to update.."

        import pip

        try:
            from git import Git
        except ImportError:
            pip.main(["install", "gitpython==0.1.7", "gitdb", "async"])
            from git import Git

        g = Git(".")
        g.pull()
        pip.main(["install", "-r", "requirements.txt"])
        print "Done!"
    except Exception as e:
        print "Error updating: %s" % e
        raise e

    exit(0)

if __name__ == "__main__":
    if os.path.dirname(sys.argv[0]):
        os.chdir(os.path.dirname(sys.argv[0]))

    from utils.log import getLogger, open_log, close_log
    from utils.misc import output_exception
    from system.factory_manager import Manager
    from system import constants
    from system import decorators

    sys.stdout = getwriter('utf-8')(sys.stdout)
    sys.stderr = getwriter('utf-8')(sys.stderr)

    if not os.path.exists("logs"):
        os.mkdir("logs")

    open_log("output.log")

    logger = getLogger("System")

    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)

    logger.info("Starting up, version \"%s\"" % constants.__version__)

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
            decorators.pool.stop()

            if "--no-catch" not in sys.argv:
                raw_input("Press enter to exit.")
        except:
            pass
