__author__ = 'Gareth Coles'

import os

from distutils.version import StrictVersion

from system.constants import __release__ as current
from system.singleton import Singleton

from utils.log import getLogger

versions = {
    "1.0.0": "Default, this will never be shown",
    "1.1.0: (
        "============= Version {VERSION} =============\n"
        "\n"
        "This release requires you to update your\n"
        "plugins - please do so or they may break!"
    )
}


class VersionManager(object):
    __metaclass__ = Singleton

    current = ""
    stored = ""

    current_v = None
    stored_v = None

    def __init__(self):
        self.log = getLogger("Updates")
        self.current = current
        self.current_v = StrictVersion(current)

        self.load_release()
        self.do_warnings()

    def do_warnings(self):
        updated = False

        for version in versions.keys():
            release = StrictVersion(version)

            if self.stored_v < release <= self.current_v:
                updated = True
                message = versions.get(version)

                for line in message.split("\n"):
                    self.log.info(line.replace("{VERSION}", version))
                self.log.info("")

        if updated:
            self.current = self.current
            self.current_v = StrictVersion(current)
            self.write_release()
        else:
            self.log.info("No update messages detected.")

        self.log.info("Current release: %s" % self.current)

    def load_release(self):
        if not os.path.exists("version"):
            self.stored = self.current
            self.stored_v = self.current_v
            self.write_release()
            return

        self.stored = open("version").read().strip(" \n\r")
        self.stored_v = StrictVersion(self.stored)

    def write_release(self):
        fh = open("version", "w")
        fh.write(self.current)
        fh.flush()
        fh.close()
