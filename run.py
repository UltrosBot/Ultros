#!/usr/bin/env python
# coding=utf-8

#                  === BEGIN LICENSE BLOCK ===                  #
#                                                               #
# Ultros is distributed under the Artistic License 2.0.         #
# You should have received a copy of this license with Ultros,  #
# but if you didn't, you can find one at the following link:    #
#                                                               #
#          http://choosealicense.com/licenses/artistic/         #
#                                                               #
#                  ===  END LICENSE BLOCK  ===                  #

"""
Ultros - That squidoctopus bot thing.

This is the main file - You run this! Importing it is a bad idea!
Stuff like that!

Don't forget to read the README, the docs and the LICENSE before you even
consider modifying or distributing this software.

If, however, you do fork yourself a copy and make some changes, submit a
pull request or otherwise get in contact with us - we'd love your help!
"""

import argparse
import logging
import os
import sys

from kitchen.text.converters import getwriter

from system.translations import Translations


DESC = "Ultros - that squidoctopus bot thing"

p = argparse.ArgumentParser(description=DESC)
p.add_argument("--debug", help="Enable debug output", action="store_true")
p.add_argument("-l", "--language", help="Specify which language to use for "
                                        "console and logging messages")
p.add_argument("-ml", "--mlanguage", help="Specify which language to use for "
                                          "chat messages")
p.add_argument("-u", "--update", help="Run an update and quit",
               action="store_true")
p.add_argument("-n", "--no-catch",
               help="Exit immediately instead of waiting for someone to press "
                    "enter",
               action="store_true")
p.add_argument("--loop",
               help="Loop infinitely, updating automatically and restarting "
                    "whenever the bot is shutdown.",
               action="store_true")

args = p.parse_args()
trans = Translations(args.language, args.mlanguage)

_ = trans.get()


def update():
    try:
        print _("Attempting to update..")

        import pip

        try:
            from git import Git
        except ImportError:
            pip.main(["install", "gitpython==0.1.7", "gitdb", "async"])
            from git import Git

        g = Git(".")
        g.pull()

        import packages

        packages.setup()
        print _("Done!")
    except Exception as e:
        print _("Error updating: %s") % e
        raise e

    exit(0)


def main():
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

    logger.info(_("Starting up, version \"%s\"") % constants.__version__)

    # Write PID to file
    fh = open("ultros.pid", "w")
    fh.write(str(os.getpid()))
    fh.flush()
    fh.close()

    logger.info(_("PID: %s") % os.getpid())

    manager = None

    try:
        manager = Manager()
        manager.run()

    except Exception:
        logger.critical(_("Runtime error - process cannot continue!"))
        output_exception(logger)
    except SystemExit as e:
        close_log("output.log")
        decorators.pool.stop()
        os.remove("ultros.pid")
        exit(e.code)
    finally:
        try:
            manager.unload()
            close_log("output.log")
            decorators.pool.stop()
            os.remove("ultros.pid")

            if not args.no_catch:
                raw_input(_("Press enter to exit."))
        except Exception:
            pass

if args.update:
    update()
else:
    if args.loop:
        while True:
            main()
    else:
        main()
