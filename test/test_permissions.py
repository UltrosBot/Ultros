__author__ = 'Gareth Coles'

"""
Tests for the permissions manager in the auth plugin.
"""

# Imports

import os
import tempfile
import shutil
import yaml

import nose.tools as nosetools

from plugins.auth.permissions_handler import permissionsHandler
from system.plugin import PluginObject
from system.storage import formats
from system.storage.manager import StorageManager

from utils.log import getLogger

tmpdir = tempfile.mkdtemp()


class TestPlugin(PluginObject):
    data = None
    logger = None
    storage = None

    handler = None

    confdir = ""
    datadir = ""

    def setup(self):
        pass

    def __init__(self):
        self.logger = getLogger("Permissions")

        self.confdir = tmpdir + "/config/"
        self.datadir = tmpdir + "/data/"

        try:
            os.makedirs(self.confdir)
            os.makedirs(self.datadir)
            self.logger.debug("Config and data dirs created.")
        except Exception:
            pass

        yaml.dump({"editor_warning": False},
                  open(self.confdir + "settings.yml", "w"))

        self.storage = StorageManager(self.confdir, self.datadir)

        self.data = self.storage.get_file(self, "data", formats.YAML,
                                          "permissions.yml")

        self.handler = permissionsHandler(self, self.data)

        super(PluginObject, self).__init__()

    @classmethod
    def teardown_class(cls):
        del cls.data
        del cls.storage
        del cls.handler

        shutil.rmtree(tmpdir)

    # Actual tests

    def test_additions(self):
        """
        PERMS | Test permissions handler addition functions\n
        """

    def test_deletions(self):
        """
        PERMS | Test permissions handler deletion functions\n
        """

    def test_modifications(self):
        """
        PERMS | Test permissions handler modification functions\n
        """

    def test_reads(self):
        """
        PERMS | Test permissions handler reading functions\n
        """
        with self.data:
            self.data["groups"] = {}
            self.data["users"] = {}

            self.data["groups"]["default"] = {
                "options": {"lerp": "gerp"},
                "permissions": ["nose.test"],
                "protocols": {"nose-test": {
                    "permissions": [
                        "nose.test2",
                        "/g[A-Za-z].*2002/"
                    ],
                    "sources": {
                        "#nose": ["nose.test3"]
                    }
                }}
            }

            self.data["groups"]["inherits"] = {
                "options": {},
                "permissions": [],
                "protocols": {},
                "inherit": "default"
            }

            self.data["users"]["test"] = {
                "group": "default",
                "options": {
                    "superadmin": False
                },
                "permissions": ["nose.test"],
                "protocols": {"nose-test": {
                    "permissions": ["nose.test2"],
                    "sources": {
                        "#nose": ["nose.test3"]
                    }
                }}
            }

            self.logger.debug("[READING] Dummy data set up.")

        # Group tests

        self.logger.debug("[READING] Testing: Group options")

        nosetools.eq_(self.handler.get_group_option("default", "derp"),
                      None)
        nosetools.eq_(self.handler.get_group_option("default", "lerp"),
                      "gerp")
        nosetools.eq_(self.handler.get_group_option("herp", "derp"),
                      False)

        self.logger.debug("[READING] Testing: Group inheritance")

        nosetools.eq_(self.handler.get_group_inheritance("default"),
                      None)
        nosetools.eq_(self.handler.get_group_inheritance("inherits"),
                      "default")
        nosetools.eq_(self.handler.get_group_inheritance("herp"),
                      False)

        self.logger.debug("[READING] Testing: Group permissions")

        self.logger.debug("[READING] -- Permissions in their containers")
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "nose.test"),
                      True)
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "nose.test2",
                                                        "nose-test"),
                      True)
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "gDroid2002",
                                                        "nose-test"),
                      True)
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "nose.test3",
                                                        "nose-test",
                                                        "#nose"),
                      True)

        self.logger.debug("[READING] -- Cascading permissions")
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "nose.test",
                                                        "nose-test"),
                      True)
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "nose.test",
                                                        "nose-test",
                                                        "#nose"),
                      True)
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "nose.test2",
                                                        "nose-test",
                                                        "#nose"),
                      True)

        self.logger.debug("[READING] -- False permissions")
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "nose.untest"),
                      False)
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "nose.untest",
                                                        "nose-test"),
                      False)
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "g100d2002",
                                                        "nose-test"),
                      False)
        nosetools.eq_(self.handler.group_has_permission("default",
                                                        "nose.untest",
                                                        "nose-test",
                                                        "#nose"),
                      False)

        self.logger.debug("[READING] -- Inherited permissions")
        self.logger.debug("[READING]    -- Permissions in their containers")
        nosetools.eq_(self.handler.group_has_permission("inherits",
                                                        "nose.test"),
                      True)
        nosetools.eq_(self.handler.group_has_permission("inherits",
                                                        "nose.test2",
                                                        "nose-test"),
                      True)
        nosetools.eq_(self.handler.group_has_permission("inherits",
                                                        "nose.test3",
                                                        "nose-test",
                                                        "#nose"),
                      True)
        self.logger.debug("[READING]    -- Cascading permissions")
        nosetools.eq_(self.handler.group_has_permission("inherits",
                                                        "nose.test",
                                                        "nose-test"),
                      True)
        nosetools.eq_(self.handler.group_has_permission("inherits",
                                                        "nose.test",
                                                        "nose-test",
                                                        "#nose"),
                      True)
        nosetools.eq_(self.handler.group_has_permission("inherits",
                                                        "nose.test2",
                                                        "nose-test",
                                                        "#nose"),
                      True)

        self.logger.debug("[READING]    -- False permissions")
        nosetools.eq_(self.handler.group_has_permission("inherits",
                                                        "nose.untest"),
                      False)
        nosetools.eq_(self.handler.group_has_permission("inherits",
                                                        "nose.untest",
                                                        "nose-test"),
                      False)
        nosetools.eq_(self.handler.group_has_permission("inherits",
                                                        "nose.untest",
                                                        "nose-test",
                                                        "#nose"),
                      False)

        self.logger.debug("[READING] -- Impossible permissions")
        nosetools.eq_(self.handler.group_has_permission("gerp",
                                                        "nose.test"),
                      False)
        nosetools.eq_(self.handler.group_has_permission("gerp",
                                                        "nose.test",
                                                        "nose-test"),
                      False)
        nosetools.eq_(self.handler.group_has_permission("gerp",
                                                        "nose.test",
                                                        "nose-test",
                                                        "#nose"),
                      False)

        self.logger.debug("[READING] Tests complete.")

    def test_full(self):
        """
        PERMS | Test typical permissions handler usage
        """
