# coding=utf-8

__author__ = 'Gareth Coles'

from system.help.topics.generic import Topic
from system.enums import HelpTopicType


class CommandTopic(Topic):
    command = ""
    plugin = ""
    syntax = ""
    usage = ""

    def __init__(self, command, plugin, syntax, usage):
        self.syntax = syntax
        self.validate_syntax()

        self.command = command
        self.plugin = plugin
        self.usage = usage

        name = "%s/%s" % (plugin, command)
        super(CommandTopic, self).__init__(name, HelpTopicType.CommandTopic)

    def validate_syntax(self):
        for part in self.syntax:
            if not isinstance(part, Argument):
                raise ValueError(
                    "Invalid command syntax: Must be a list of Argument "
                    "objects"
                )
        return True

    def __str__(self):
        return "{CHARS}%s %s\n%s" % (
            self.command,
            " ".join([str(x) for x in self.syntax]),
            self.usage
        )


class Argument(object):
    name = ""
    info = ""

    def __init__(self, name, info=""):
        self.name = name
        self.info = info

    def __str__(self):
        return self.name


class RequiredArgument(Argument):
    def __str__(self):
        return "<%s>" % self.name


class OptionalArgument(Argument):
    def __str__(self):
        return "[%s]" % self.name


class RequiredArgumentWithSpaces(RequiredArgument):
    def __str__(self):
        return "<\"%s\">" % self.name


class OptionalArgumentWithSpaces(OptionalArgument):
    def __str__(self):
        return "[\"%s\"]" % self.name
