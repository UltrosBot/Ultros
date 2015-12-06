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
import locale
import logging
import os
import sys

import lib  # noqa

from kitchen.text.converters import getwriter
from twisted.python import log as twisted_log

from system.core import Ultros
from system.translations import Translations
from system.versions import VersionManager


observer = twisted_log.PythonLoggingObserver(loggerName='Twisted')
observer.start()

# Attempt to guess the locale
locale.setlocale(locale.LC_ALL, "")

DESC = "Ultros - that squidoctopus bot thing"

p = argparse.ArgumentParser(description=DESC)
p.add_argument("-l", "--language", help="Specify which language to use for "
                                        "console and logging messages")
p.add_argument("-ml", "--mlanguage", help="Specify which language to use for "
                                          "chat messages")
p.add_argument("-u", "--update", help="Run an update and quit",
               action="store_true")
p.add_argument("-c", "--catch",
               help="Don't exit immediately; useful for Windows users",
               action="store_true")
p.add_argument("-prd", "--pycharm-remote-debug",
               help="Enable PyCharm remote debugging on port 20202. "
                    "Takes a hostname as an argument. This requires you to "
                    "have pycharm-debug.egg in your Python PATH. If you don't "
                    "know what this means, then you don't need to use this.")
p.add_argument("-nu", "--no-upgrade",
               help="Disable the automatic in-virtualenv update run every"
                    "time the bot starts up in a virtualenv or pyenv",
               action="store_true")
p.add_argument(
    "-d", "--debug", help="Force-enable debug logging", action="store_true"
)
p.add_argument(
    "-t", "--trace", help="Force-enable trace logging", action="store_true"
)

args = p.parse_args()
trans = Translations(args.language, args.mlanguage)

if args.pycharm_remote_debug:
    import pydevd
    pydevd.settrace(
        args.pycharm_remote_debug, port=20202,
        stdoutToServer=True, stderrToServer=True
    )

_ = trans.get()


def is_virtualenv():
    if hasattr(sys, "real_prefix"):
        return True  # Virtualenv

    # PyEnv
    return hasattr(sys, "base_prefix") and sys.base_prefix == sys.prefix


def update(git=True):
    try:
        print(_("Attempting to update.."))

        if git:
            import subprocess

            r_code = subprocess.call(["git", "pull"])
            if r_code:
                print(_("It looks like git failed to run - do you have it "
                        "installed?"))

        try:
            import ensurepip
            ensurepip.bootstrap()
        except RuntimeError:
            print(_("It looks like ensurepip is disabled, continuing.."))

        import pip
        pip.main(["install", "-r", "requirements.txt", "--upgrade"])

        print(_("Done!"))
    except Exception as e:
        print(_("Error updating: %s") % e)
        raise e


def main():
    if (not args.no_upgrade) and is_virtualenv():
        update(git=False)

    if os.path.dirname(sys.argv[0]):
        os.chdir(os.path.dirname(sys.argv[0]))

    from system.logging.logger import getLogger
    from system import constants
    from system.decorators import threads

    sys.stdout = getwriter('utf-8')(sys.stdout)
    sys.stderr = getwriter('utf-8')(sys.stderr)

    ultros = Ultros(args)
    versions = VersionManager()

    if not os.path.exists("logs"):
        os.mkdir("logs")

    logger = getLogger("System")

    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)

    logger.info(_("Starting up, version \"%s\"") % constants.__version__)
    logger.info(constants.__version_info__)

    # Write PID to file
    fh = open("ultros.pid", "w")
    fh.write(str(os.getpid()))
    fh.flush()
    fh.close()

    logger.info(_("PID: %s") % os.getpid())

    try:
        logger.debug("Starting..")
        ultros.start()

    except Exception:
        logger.critical(_("Runtime error - process cannot continue!"))
        logger.exception("")
    except SystemExit as e:
        logger.trace("SystemExit caught!")

        logger.debug("Stopping threadpool..")
        threads.pool.stop()

        logger.debug("Removing pidfile..")
        os.remove("ultros.pid")
        exit(e.code)
    finally:
        try:
            logger.debug("Unloading manager..")
            ultros.stop()

            logger.debug("Stopping threadpool..")
            threads.pool.stop()

            logger.debug("Removing pidfile..")
            os.remove("ultros.pid")

            if args.catch:
                raw_input(_("Press enter to exit."))
        except Exception:
            pass

if args.update:
    update()
else:
    main()
