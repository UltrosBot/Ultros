__author__ = 'Gareth Coles'

"""Tests for the command manager"""

import logging
import nose

import nose.tools as nosetools
from mock import MagicMock as Mock

from system.command_manager import CommandManager
from system.enums import CommandState


class test_commands:

    def __init__(self):
        self.manager = CommandManager()
        self.manager.logger.setLevel(logging.CRITICAL)  # Shut up, logger

        self.factory_manager = Mock(name="factory_manager")
        self.plugin = Mock(name="plugin")

    @nosetools.nottest
    def teardown(self):
        # Clean up
        self.manager.commands = {}
        self.manager.aliases = {}
        self.manager.auth_handler = None
        self.manager.perm_handler = None

        self.plugin.reset_mock()
        self.plugin.handler.reset_mock()

        self.factory_manager.reset_mock()

    @nose.with_setup(teardown=teardown)
    def test_singleton(self):
        """CMNDS | Test Singleton metaclass"""
        nosetools.assert_true(self.manager is CommandManager())

    @nose.with_setup(teardown=teardown)
    def test_set_factory_manager(self):
        """CMNDS | Test setting factory manager"""
        self.manager.set_factory_manager(self.factory_manager)
        nosetools.assert_true(self.factory_manager)

    @nose.with_setup(teardown=teardown)
    def test_add_command(self):
        """CMNDS | Test adding commands"""
        r = self.manager.register_command("test", self.plugin.handler,
                                          self.plugin, "test.test",
                                          ["test2"], True)

        nosetools.assert_true(r)
        nosetools.assert_true("test" in self.manager.commands)

        command = self.manager.commands.get("test", None)

        if command:
            nosetools.assert_true("f" in command)
            nosetools.assert_true(command.get("f") is self.plugin.handler)

            nosetools.assert_true("permission" in command)
            nosetools.assert_true(command.get("permission") == "test.test")

            nosetools.assert_true("owner" in command)
            nosetools.assert_true(command.get("owner") is self.plugin)

            nosetools.assert_true("default" in command)
            nosetools.assert_true(command.get("default"))

        nosetools.assert_true("test2" in self.manager.aliases)

        alias = self.manager.aliases.get("test2", None)

        if alias:
            nosetools.assert_true(alias == "test")

        r = self.manager.register_command("test", self.plugin.handler,
                                          self.plugin, "test.test",
                                          ["test2"], True)

        nosetools.assert_false(r)

    @nose.with_setup(teardown=teardown)
    def test_unregister_commands(self):
        """CMNDS | Test unregistering commands"""
        self.manager.register_command("test1", self.plugin.handler,
                                      self.plugin, aliases=["test11"])
        self.manager.register_command("test2", self.plugin.handler,
                                      self.plugin, aliases=["test22"])
        self.manager.register_command("test3", self.plugin.handler,
                                      self.plugin, aliases=["test33"])

        nosetools.assert_equals(len(self.manager.commands), 3)
        nosetools.assert_equals(len(self.manager.aliases), 3)

        self.manager.unregister_commands_for_owner(self.plugin)

        nosetools.assert_equals(len(self.manager.commands), 0)
        nosetools.assert_equals(len(self.manager.aliases), 0)

    @nose.with_setup(teardown=teardown)
    def test_run_commands_defaults(self):
        """CMNDS | Test running commands directly | Defaults"""

        self.manager.register_command("test4", self.plugin.handler,
                                      self.plugin, aliases=["test5"],
                                      default=True)

        caller = Mock(name="caller")
        source = Mock(name="source")
        protocol = Mock(name="protocol")

        # Testing defaults

        r = self.manager.run_command("test4", caller, source, protocol, "")
        nosetools.assert_equals(r, (CommandState.Success, None))

        r = self.manager.run_command("test5", caller, source, protocol, "")
        nosetools.assert_equals(r, (CommandState.Success, None))

        nosetools.assert_equals(self.plugin.handler.call_count, 2)

    @nose.with_setup(teardown=teardown)
    def test_run_commands_aliases(self):
        """CMNDS | Test running commands directly | Aliases"""

        self.manager.register_command("test4", self.plugin.handler,
                                      self.plugin, aliases=["test5"],
                                      default=True)

        caller = Mock(name="caller")
        source = Mock(name="source")
        protocol = Mock(name="protocol")

        # Testing defaults

        r = self.manager.run_command("test4", caller, source, protocol, "")
        nosetools.assert_equals(r, (CommandState.Success, None))

        self.plugin.handler.assert_called_with(protocol, caller, source,
                                               "test4", "", [])

        # Reset mock
        self.plugin.handler.reset_mock()

        r = self.manager.run_command("test5", caller, source, protocol, "")
        nosetools.assert_equals(r, (CommandState.Success, None))

        self.plugin.handler.assert_called_with(protocol, caller, source,
                                               "test4", "", [])

        # Reset mock
        self.plugin.handler.reset_mock()

        self.manager.register_command("test5", self.plugin.handler,
                                      self.plugin, default=True)

        r = self.manager.run_command("test5", caller, source, protocol, "")
        nosetools.assert_equals(r, (CommandState.Success, None))

        self.plugin.handler.assert_called_with(protocol, caller, source,
                                               "test5", "", [])

    @nose.with_setup(teardown=teardown)
    def test_run_commands_auth(self):
        """CMNDS | Test running commands directly | Auth"""

        caller = Mock(name="caller")
        source = Mock(name="source")
        protocol = Mock(name="protocol")

        auth = Mock(name="auth")
        perms = Mock(name="perms")

        self.manager.set_auth_handler(auth)
        self.manager.set_permissions_handler(perms)

        # COMMAND WITH PERMISSION #
        auth.authorized.return_value = True
        perms.check.return_value = True

        self.manager.register_command("test5", self.plugin.handler,
                                      self.plugin, "test.test",
                                      aliases=["test6"])

        r = self.manager.run_command("test5", caller, source, protocol, "")

        nosetools.assert_equals(r, (CommandState.Success, None))
        nosetools.assert_equals(self.plugin.handler.call_count, 1)

        auth.authorized.reset_mock()
        perms.check.reset_mock()
        self.plugin.handler.reset_mock()

        # ALIAS WITH PERMISSION #

        r = self.manager.run_command("test6", caller, source, protocol, "")

        nosetools.assert_equals(r, (CommandState.Success, None))
        nosetools.assert_equals(self.plugin.handler.call_count, 1)

        auth.authorized.reset_mock()
        perms.check.reset_mock()

        auth.authorized.return_value = True
        perms.check.return_value = False
        self.plugin.handler.reset_mock()

        # COMMAND WITHOUT PERMISSION #

        r = self.manager.run_command("test5", caller, source, protocol, "")

        nosetools.assert_equals(r, (CommandState.NoPermission, None))
        nosetools.assert_equals(self.plugin.handler.call_count, 0)

        perms.check.return_value = True

        auth.authorized.reset_mock()
        perms.check.reset_mock()
        self.plugin.handler.reset_mock()

        # COMMAND WITH EXCEPTION #

        self.plugin.handler = Mock(side_effect=Exception('Boom!'))
        self.manager.unregister_commands_for_owner(self.plugin)

        self.manager.register_command("test5", self.plugin.handler,
                                      self.plugin, "test.test")

        r = self.manager.run_command("test5", caller, source, protocol, "")

        nosetools.assert_equals(r[0], CommandState.Error)
        nosetools.assert_true(isinstance(r[1], Exception))
        nosetools.assert_equals(self.plugin.handler.call_count, 1)

        auth.authorized.reset_mock()
        perms.check.reset_mock()
        self.plugin.handler.reset_mock()

        # UNKNOWN COMMAND #

        r = self.manager.run_command("test7", caller, source, protocol, "")
        nosetools.assert_equals(r, (CommandState.Unknown, None))
        nosetools.assert_equals(self.plugin.handler.call_count, 0)
